
%% untar ERA5 downscaled data
% imfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\data\permafrost\LST\era5downscaled";
% imfiles = dir(fullfile(imfolder, '*.tar'));
% imuntarfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\data\permafrost\LST\era5downscaled";


% if ~exist(imuntarfolder, 'dir')
%     mkdir(imuntarfolder);
% end

% parfor i = 1:length(imfiles)
%     fprintf('Extracting %d/%d: %s\n', i, length(imfiles), imfiles(i).name);
%     imfile = fullfile(imfolder, imfiles(i).name);
%     untar(imfile, imuntarfolder);
% end

%% prepare folder and file paths
clearvars
tic
imfolder_landsat  = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\data\permafrost\LST\LandsatLST";
imfolder_era5     = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\data\permafrost\LST\era5downscaled";
imfolder_landmask = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\data\permafrost\LST\landmask";
imfolder_merged   = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\data\permafrost\LST\mergedLST";
% roi = "Aasiaat";
% roi = "Disko";
% roi = "Ilulissat";
% roi = "Kangerlussuaq";
% roi = "Kobbefjord";
roi = "Zackenberg";
% Create merged folder for the specific ROI if it doesn't exist
merged_roi_folder = fullfile(imfolder_merged, roi);
if ~exist(merged_roi_folder, 'dir')
    mkdir(merged_roi_folder);
    fprintf('Created directory: %s\n', merged_roi_folder);
end

imfiles_era5 = dir(fullfile(imfolder_era5, roi, '**', 't2m_elvcorr*.nc'));
imfiles_landsat = dir(fullfile(imfolder_landsat, roi, '**', '*.tif'));
imfile_landmask = fullfile(imfolder_landmask, 'GreenlandMask_' + roi + '.tif');
imfile_dem = fullfile(imfolder_landmask, 'ArcticDEM_' + roi + '.tif');

%% Load calibration coefficients
calibcoeff_landsat = readtable("../GEMLST_Landsat/landsat_calibration_parameters.txt");
calibcoeff_era5 = readtable("../climate/era5_calibration_parameters.txt");
%% merge ERA5 and Landsat data
% read landmask: 0 for water, 1 for land
[landmask, R] = readgeoraster(imfile_landmask, 'OutputType', 'uint8');
% read DEM
imdata_dem = readgeoraster(imfile_dem, 'OutputType', 'double');

for i = 1:length(imfiles_era5)
    imfile_era5 = fullfile(imfiles_era5(i).folder, imfiles_era5(i).name);
    fprintf('%d: %s\n', i, imfiles_era5(i).name);
    % Read the full t2m data
    imdata_era5 = ncread(imfile_era5, 't2m');
    % Extract the dimensions we want (keeping dimension 3 at index 1)
    imdata_era5 = squeeze(imdata_era5(:,:,1,:));
    % Get coordinate information
    X = ncread(imfile_era5, 'X');
    Y = ncread(imfile_era5, 'Y');
    imtime_era5 = ncread(imfile_era5, 'time');
    imtime_era5 = datetime(1850,1,1) + days(imtime_era5);
    imtime_era5_str = imtime_era5;
    imtime_era5_str.Format = 'yyyy-MM-dd';
    imtime_era5_str = string(imtime_era5_str);
    
    % process LST day by day
    for j = 1:numel(imtime_era5_str)

        fprintf('Processing image in %s on %s\n', roi, imtime_era5_str(j));
        imdata_era5_day = imdata_era5(:,:,j)' - 273.15;
        % check if the size of era5 data is the same as landmask
        if size(imdata_era5_day) ~= size(landmask)
            fprintf('Extent of ERA5 Land is different from LandsatLST, interpolating ERA5 grids now.\n');
            [Xa, Ya] = meshgrid((R.XWorldLimits(1)+15):30:(R.XWorldLimits(2)-15), (R.YWorldLimits(2)-15):-30:(R.YWorldLimits(1)+15));
            [Xb, Yb] = projfwd(R.ProjectedCRS, Y', X');
            imdata_era5_day = griddata(Xb, Yb, imdata_era5_day, Xa, Ya, 'nearest');
        end
        % data harmonization by AWS dervied coefficient
        imdata_era5_day = imdata_era5_day * calibcoeff_era5.coefficient + calibcoeff_era5.intercept;
        
        imflag = uint16(landmask) * 2; % 0 for water, 1 for landsat, 2 for era5

        % find the corresponding Landsat image
        imfile_landsat = fullfile(imfolder_landsat, roi, 'GEMLST_Landsat_' + imtime_era5_str(j) + '.tif');
        if isfile(imfile_landsat)
            fprintf('Landsat image found\n');
            imdata_landsat = readgeoraster(imfile_landsat, 'OutputType', 'double');
            imflag(imdata_landsat > 0 & landmask > 0) = 1;
            imdata_landsat(imdata_landsat == 0) = nan;
            % rescale data to celsius degree
            imdata_landsat = imdata_landsat * 0.00341802 + 149 - 273.15;
            % data harmonization by AWS dervied coefficient
            imdata_landsat = imdata_landsat * calibcoeff_landsat.coefficient + calibcoeff_landsat.intercept;
        else
            fprintf('Landsat image not found\n');
            imdata_landsat = imdata_era5_day;
        end
        
        % merge the two datasets and apply landmask
        imdata_merged = imdata_landsat;
        imdata_merged(isnan(imdata_landsat)) = imdata_era5_day(isnan(imdata_landsat));
        imdata_merged(landmask == 0) = nan;

        % visualize the data
        fig1 = figure('Visible', 'off');
        fig1.Position = [100 100 1200 400];
        t = tiledlayout(1, 3, "TileSpacing","compact", "Padding","compact");
        ax1 = nexttile;
        if isfile(imfile_landsat)
            mapshow(ax1, imdata_landsat, R, 'DisplayType', 'surface');
            hold on
            scalebarpsn('location', 'se');
            colormap(ax1, cmocean('thermal'));
            clim(ax1, [-30 30]);
            title('Landsat LST');
        else
            mapshow(ax1, imdata_landsat, R, 'DisplayType', 'surface');
            hold on
            scalebarpsn('location', 'se');
            colormap(ax1, cmocean('thermal'));
            clim(ax1, [-30 30]);
            title('Landsat LST not available');
        end
        ax2 = nexttile;
        mapshow(ax2, imdata_era5_day, R, 'DisplayType', 'surface');
        hold on
        scalebarpsn('location', 'se');
        colormap(ax2, cmocean('thermal'));
        clim(ax2, [-30 30]);
        title('ERA5 LST');
        ax3 = nexttile;
        mapshow(ax3, imdata_merged, R, 'DisplayType', 'surface');
        hold on
        scalebarpsn('location', 'se');
        colormap(ax3, cmocean('thermal'));
        clim(ax3, [-30 30]);
        title('Merged LST');
        title(t, roi + ' ' + imtime_era5_str(j));
        % Add a common colorbar at the southwest position of the layout
        cb = colorbar(ax3, 'Location', 'southoutside');
        cb.Layout.Tile = 'south'; % Place at the bottom of the layout
        cb.Label.String = 'Temperature (°C)';
        fontsize(t, scale=1.2);
        % Save the figure
        figfile = fullfile(merged_roi_folder, 'LandsatERA5mergedLST_' + imtime_era5_str(j) + '.png');
        exportgraphics(fig1, figfile, 'Resolution', 300);
        close(fig1);
        
        % save the merged data
        % rescale data to original scale and convert to uint16
        imdata_merged = (imdata_merged + 273.15 - 149) / 0.00341802;
        imdata_merged = uint16(imdata_merged);
        % add imflag as band 2
        imdata_merged(:,:,2) = imflag;
        imfile_merged = fullfile(merged_roi_folder, 'LandsatERA5mergedLST_' + imtime_era5_str(j) + '.tif');
        geotiffwrite(imfile_merged, imdata_merged, R, 'CoordRefSysCode', 3413);
        fprintf('Saved merged image to %s\n', imfile_merged);
    end
    
end

elapsed_time = toc;
fprintf('Done! Elapsed time is %s\n', string(duration(seconds(elapsed_time),'Format','hh:mm:ss')));
