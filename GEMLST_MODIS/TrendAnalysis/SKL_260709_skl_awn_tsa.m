%5 july 2026
%Authors: Simon Kleiner, Andreas Westergaard-Nielsen
%Purpose: Monthly Mann Kendall

% input / output folders
inDir  = '/media/sfm/Local Data/SimonKleiner/GEMLST/Gapfilled/';
outDir = '/media/sfm/Local Data/SimonKleiner/GEMLST/Gapfilled/monthly/';

% list files and extract date substring (adjust indices if your filenames differ)
files = dir(fullfile(inDir, '*.tiff'));
names = {files.name}';
fileIndex = cellfun(@(s) s(8:15), names, 'UniformOutput', false); % 'yyyyMMdd'

% convert to datetime (keep as datetime, not datenum)
dateFormat = 'yyyyMMdd';
dates = datetime(fileIndex, 'InputFormat', dateFormat);

% loop years
for yr = 2000:2025
    sel = year(dates) == yr;
    namesYear = names(sel);
    datesYear = dates(sel);

    % group by month and compute monthly averages
    for m = 1:12
        idx = month(datesYear) == m;
        monthFiles = namesYear(idx);
        if isempty(monthFiles)
        %print the missing filename
        fprintf('Missing files for year %d, month %02d\n', yr, m);
            continue
        end

        % read first file to get size, class and spatial ref
        [A0, R] = readgeoraster(fullfile(inDir, monthFiles{1}), Bands=1);
        class0 = class(A0);
        acc = double(A0);        % accumulator in double
        count = 1;

        % loop remaining files
        for k = 2:numel(monthFiles)
            [Ak, ~] = readgeoraster(fullfile(inDir, monthFiles{k}), Bands=1);
            acc = acc + double(Ak);
            count = count + 1;
        end

        avgImg = acc / count;

        % convert back to original class with rounding/clipping if integer
        if isinteger(A0)
            avgImg = round(avgImg);
            switch class0
                case 'uint8', lim = [0 255];
                case 'uint16', lim = [0 65535];
                case 'int16', lim = [-32768 32767];
                otherwise, lim = [];
            end
            if ~isempty(lim)
                avgImg = min(max(avgImg, lim(1)), lim(2));
            end
            outImg = cast(avgImg, class0);
        else
            outImg = avgImg;
        end

        % write GeoTIFF preserving spatial reference
        outName = sprintf('GEMLST_monthly_%d_%02d.tif', yr, m);
        outPath = fullfile(outDir, outName);

        %geotiffwrite(outPath, outImg, R, CoordRefSysCode=3413);

    end
end



% clear memory
clear;
outDir = '/media/sfm/Local Data/SimonKleiner/GEMLST/Gapfilled/monthly/';
% list monthly files
filesMonths = dir(fullfile(outDir, '*.tif'));

% ensure files are sorted (important for temporal order)
[~,sortIdx] = sort({filesMonths.name});
filesMonths = filesMonths(sortIdx);

% Create fileDates
names = {filesMonths.name}';
tok = regexp(names, '(\d{4}_\d{2})', 'match', 'once');
clean = cellfun(@(s) strrep(s, '_', ''), tok, 'UniformOutput', false);
fileDates = datetime(clean, 'InputFormat', 'yyyyMM'); 

% read one file to get grid size / class / ref
[A0, R0] = readgeoraster(fullfile(outDir, filesMonths(1).name));
gridSize = size(A0);

% preallocate datacube: [rows, cols, nMonths]
monthlyDataCube = zeros([gridSize, numel(filesMonths)], 'double');

% read files consecutively and add to datacube
for i = 1:numel(filesMonths)
    fname = fullfile(outDir, filesMonths(i).name);
    [Ai, ~] = readgeoraster(fname);
    monthlyDataCube(:,:,i) = double(Ai);   % convert to double for analysis
end

% Save to disk for memory-mapped access
outDir = '/media/sfm/Local Data/SimonKleiner/GEMLST/Gapfilled/monthly/';
matfile = fullfile(outDir, 'monthlyDataCube.mat');
save(matfile, 'monthlyDataCube', 'fileDates', 'R0', '-v7.3');


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% If the "pool" exists, delete the parallel pool
delete(pool);
clear;
ResDir = '/media/sfm/Local Data/SimonKleiner/Results/';

% analysis for trends
% monthlyDataCube: [nRows, nCols, nTimes]
m = matfile('/media/sfm/Local Data/SimonKleiner/Scripts/sktt/monthlyDataCube.mat');
[nRows, nCols, nTimes] = size(m.monthlyDataCube);

% Linear index loop for parfor
numPix = nRows * nCols;

tauseaVec = nan(numPix,1);
sigAdjVec   = nan(numPix,1);

% Adjust number of workers (default 20)
pool = parpool('local', 15);

% Create batches to reduce memory usage
batchSize = 1e6; % Adjust based on memory
numBatches = ceil(numPix / batchSize);

% Parameters for sktt function
alpha = 0.05;
wantplot = 0;
StartSeason = 1;

for batch = 1:numBatches
    startIdx = (batch-1)*batchSize + 1;
    endIdx = min(batch*batchSize, numPix);

    % Process batch in parallel
    parfor idx = startIdx:endIdx
        [r, c] = ind2sub([nRows, nCols], idx);
        ts = squeeze(m.monthlyDataCube(r, c, :));   % nTimes x 1

        if all(isnan(ts)), continue; end

        % load fileDates from matfile (column vector of datetimes length nTimes)
        fileDates = m.fileDates;        % allowed in parfor when reading
        
        years  = year(fileDates(:));
        months = month(fileDates(:));
        datain_ts = [years months ts];

        [taubsea tausea Sens h sig sigAdj Zs Zmod Ss Sigmas CIlower CIupper] = sktt(datain_ts, alpha, wantplot, StartSeason);
        %taubseaVec(idx) = taubsea;
        tauseaVec(idx) = tausea;
        sensVec(idx) = Sens;
        hVec(idx) = h;
        sigAdjVec(idx) = sigAdj;
        ZsVec(idx) = Zs;
        CIlowVec(idx) = CIlower;
        CIupVec(idx) = CIupper;
        %clear ts pval trendval;
    end
end


 %%% CREATE COBES FOR 3D RESULTS %%%
% Create a cube for the senslope median slope per individal season (carries
% 312 entries per pixel) and export as geotiff with 312 bands. 

numPix = nRows * nCols;

% Determine number of time steps (nTimes) from fileDates if available
if exist('fileDates','var')
    nTimes = numel(fileDates);
else
    nTimes = []; % will infer below
end

% Build 3-D cube sensCube: [nRows, nCols, nTimes]
if iscell(sensVec)
    % find first non-empty cell to infer length
    firstIdx = find(~cellfun(@isempty, sensVec), 1);
    if isempty(firstIdx), error('sensVec cell array contains only empty cells'); end
    inferredLen = numel(sensVec{firstIdx});
    if ~isempty(nTimes) && inferredLen ~= nTimes
        warning('Inferred time length (%d) differs from fileDates (%d). Using inferred.', inferredLen, nTimes);
    end
    nTimes = inferredLen;
    sensCube = nan(nRows, nCols, nTimes);
    for idx = 1:numPix
        v = sensVec{idx};
        if isempty(v), continue; end
        if numel(v) ~= nTimes
            error('sensVec{%d} length %d does not match expected nTimes=%d', idx, numel(v), nTimes);
        end
        [r,c] = ind2sub([nRows, nCols], idx);
        sensCube(r,c,:) = reshape(v, 1, 1, []);
    end
else
    % numeric vector: must be divisible into numPix * nTimes
    len = numel(sensVec);
    if isempty(nTimes)
        % infer nTimes
        if mod(len, numPix) ~= 0
            error('Cannot infer nTimes: sensVec length %d not divisible by numPix %d', len, numPix);
        end
        nTimes = len / numPix;
    else
        if len ~= numPix * nTimes
            error('sensVec length (%d) does not equal numPix(%d) * nTimes(%d)', len, numPix, nTimes);
        end
    end
    sensCube = reshape(sensVec, [nRows, nCols, nTimes]);
end

% Save results
save(fullfile(ResDir, 'sktt_results.mat'), 'sensCube', '-v7.3');

% Write multi-band GeoTIFF (bands = time steps)
% geotiffwrite accepts rows x cols x bands arrays
outPath = fullfile(ResDir, 'sensCube.tif');
geotiffwrite(outPath, sensCube, R0, 'CoordRefSysCode', 3413);


 %%% RESHAPE AND CREATE 2D MAPS OF TWO DIMENSIONAL RESULTS %%% 
% reshape the other vectors back to 2D maps (rows x cols)
tauseaMap = reshape(tauseaVec, [nRows, nCols]);
%hMap = reshape(hVec, [nRows, nCols]); output number of elements "must not
%change". h, sens and taubsea have shape 1x4280063, while many others have 4553080x1.  
pvalMap  = reshape(sigAdjVec,  [nRows, nCols]);
ZMap = reshape(ZsVec, [nRows, nCols]);
CIlowMap = reshape(CIlowVec, [nRows, nCols]);
CIupMap = reshape(CIupVec, [nRows, nCols]);

R0 = m.R0;

% Save results as MAT
save(fullfile(ResDir, 'sktt_results.mat'), 'tauseaMap', 'pvalMap', 'ZMap', 'CIlowMap', 'CIupMap', '-v7.3'); % add seastrendMap if necessary

% write GeoTIFFs (use spatial ref R0; write as double)
%geotiffwrite(fullfile(ResDir, 'tauseaMap.tif'), tauseaMap, R0, 'CoordRefSysCode', 3413);
%geotiffwrite(fullfile(ResDir, 'pvalMap.tif'), pvalMap, R0, 'CoordRefSysCode', 3413);
geotiffwrite(fullfile(ResDir, 'hMap.tif'), hMap, R0, 'CoordRefSysCode', 3413);