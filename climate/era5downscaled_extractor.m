%% untar ERA5 downscaled data
imfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA";
imfiles = dir(fullfile(imfolder, '*.tar'));
imuntarfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA\untar";


if ~exist(imuntarfolder, 'dir')
    mkdir(imuntarfolder);
end

parfor i = 1:length(imfiles)
    fprintf('Extracting %d/%d: %s\n', i, length(imfiles), imfiles(i).name);
    imfile = fullfile(imfolder, imfiles(i).name);
    untar(imfile, imuntarfolder);
end

%% aws sites

awsnames = {
    'Kobbefjord_M500'
    'Disko_T1'
    'Disko_T2'
    'Disko_T3'
    'Disko_T4'
    'Disko_AWS2'
    'Zackenberg_M2'
    'Zackenberg_M3'
    'Zackenberg_M4'
};

lat = [
    64.12248229980469
    69.27300262451172
    69.28909301757812
    69.2767105102539
    69.25126647949219
    69.25348663330078
    74.46549224853516
    74.50310516357422
    74.47307586669922
];

lon = [
    -51.37199020385742
    -53.479400634765625
    -53.43281936645508
    -53.45709991455078
    -53.49897003173828
    -53.514129638671875
    -20.563194274902344
    -20.459354400634766
    -20.552143096923828
];

awslist = table(awsnames, lat, lon, 'VariableNames', {'awsname', 'lat', 'lon'});
csvfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA";
%% Kobbefjord_M500
awsname = "Kobbefjord_M500";
aws = awslist(awslist.awsname == awsname, :);
% find all the nc files
imfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA\untar\KO30m";
imfiles = dir(fullfile(imfolder, '**', 't2m_elvcorr*.nc'));

for i = 1:length(imfiles)
    imfile = fullfile(imfiles(i).folder, imfiles(i).name);
    fprintf('%d: %s\n', i, imfiles(i).name);
    % Read the full t2m data
    imdata = ncread(imfile, 't2m');
    % Extract the dimensions we want (keeping dimension 3 at index 1)
    imdata = squeeze(imdata(:,:,1,:));
    % Get coordinate information
    X = ncread(imfile, 'X');
    Y = ncread(imfile, 'Y');
    imtime = ncread(imfile, 'time');
    
    % create a table to store time series of extracted data
    awsdata = table('Size', [length(imtime), 3], 'VariableTypes', {'string', 'datetime', 'double'}, 'VariableNames', {'awsname', 'imtime', 'airtemp'});
    awsdata.awsname = repmat(awsname, length(imtime), 1);
    awsdata.imtime = datetime(1850,1,1) + days(imtime);

    % Extract data for all time points at once using interpolation
    for j = 1:length(imtime)
        fprintf('Extracting %s %d/%d: %s\n', awsname, j, length(imtime), awsdata.imtime(j));
        awsdata.airtemp(j) = griddata(X, Y, imdata(:,:,j), aws.lon, aws.lat, 'linear');
    end
    % Save the data
    if i == 1
        writetable(awsdata, fullfile(csvfolder, 'aws_airtemp_era5land.csv'), ...
            'WriteVariableNames', true, 'WriteMode', 'overwrite');
    else
        writetable(awsdata, fullfile(csvfolder, 'aws_airtemp_era5land.csv'), ...
            'WriteVariableNames', false, 'WriteMode', 'append');
    end
end


%% Disko
awsname = "Disko_AWS2";
aws = awslist(awslist.awsname == awsname, :);

% find all the nc files
imfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA\untar\DI30m";
imfiles = dir(fullfile(imfolder, '**', 't2m_elvcorr*.nc'));

for i = 1:length(imfiles)
    imfile = fullfile(imfiles(i).folder, imfiles(i).name);
    fprintf('%d: %s\n', i, imfiles(i).name);
    % Read the full t2m data
    imdata = ncread(imfile, 't2m');
    % Extract the dimensions we want (keeping dimension 3 at index 1)
    imdata = squeeze(imdata(:,:,1,:));
    % Get coordinate information
    X = ncread(imfile, 'X');
    Y = ncread(imfile, 'Y');
    imtime = ncread(imfile, 'time');
    
    % create a table to store time series of extracted data
    awsdata = table('Size', [length(imtime), 3], 'VariableTypes', {'string', 'datetime', 'double'}, 'VariableNames', {'awsname', 'imtime', 'airtemp'});
    awsdata.awsname = repmat(awsname, length(imtime), 1);
    awsdata.imtime = datetime(1850,1,1) + days(imtime);

    % Extract data for all time points at once using interpolation
    for j = 1:length(imtime)
        fprintf('Extracting %s %d/%d: %s\n', awsname, j, length(imtime), awsdata.imtime(j));
        awsdata.airtemp(j) = griddata(X, Y, imdata(:,:,j), aws.lon, aws.lat, 'linear');
    end
    % Save the data
    writetable(awsdata, fullfile(csvfolder, 'aws_airtemp_era5land.csv'), ...
        'WriteVariableNames', false, 'WriteMode', 'append');
end

%% Zackenberg
awsname = "Zackenberg_M2";
aws = awslist(awslist.awsname == awsname, :);

% find all the nc files
imfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA\untar\ZA30m";
imfiles = dir(fullfile(imfolder, '**', 't2m_elvcorr*.nc'));

for i = 1:length(imfiles)
    imfile = fullfile(imfiles(i).folder, imfiles(i).name);
    fprintf('%d: %s\n', i, imfiles(i).name);
    % Read the full t2m data
     imdata = ncread(imfile, 't2m');
    % Extract the dimensions we want (keeping dimension 3 at index 1)
    imdata = squeeze(imdata(:,:,1,:));
    % Get coordinate information
    X = ncread(imfile, 'X');
    Y = ncread(imfile, 'Y');
    imtime = ncread(imfile, 'time');
    
    % create a table to store time series of extracted data
    awsdata = table('Size', [length(imtime), 3], 'VariableTypes', {'string', 'datetime', 'double'}, 'VariableNames', {'awsname', 'imtime', 'airtemp'});
    awsdata.awsname = repmat(awsname, length(imtime), 1);
    awsdata.imtime = datetime(1850,1,1) + days(imtime);

    % Extract data for all time points at once using interpolation
    for j = 1:length(imtime)
        fprintf('Extracting %s %d/%d: %s\n', awsname, j, length(imtime), awsdata.imtime(j));
        awsdata.airtemp(j) = griddata(X, Y, imdata(:,:,j), aws.lon, aws.lat, 'linear');
    end
    % Save the data
    writetable(awsdata, fullfile(csvfolder, 'aws_airtemp_era5land.csv'), ...
        'WriteVariableNames', false, 'WriteMode', 'append');
end

awsname = "Zackenberg_M3";
aws = awslist(awslist.awsname == awsname, :);

% find all the nc files
imfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA\untar\ZA30m";
imfiles = dir(fullfile(imfolder, '**', 't2m_elvcorr*.nc'));

for i = 1:length(imfiles)
    imfile = fullfile(imfiles(i).folder, imfiles(i).name);
    fprintf('%d: %s\n', i, imfiles(i).name);
    % Read the full t2m data
    imdata = ncread(imfile, 't2m');
    % Extract the dimensions we want (keeping dimension 3 at index 1)
    imdata = squeeze(imdata(:,:,1,:));
    % Get coordinate information
    X = ncread(imfile, 'X');
    Y = ncread(imfile, 'Y');
    imtime = ncread(imfile, 'time');
    
    % create a table to store time series of extracted data
    awsdata = table('Size', [length(imtime), 3], 'VariableTypes', {'string', 'datetime', 'double'}, 'VariableNames', {'awsname', 'imtime', 'airtemp'});
    awsdata.awsname = repmat(awsname, length(imtime), 1);
    awsdata.imtime = datetime(1850,1,1) + days(imtime);

    % Extract data for all time points at once using interpolation
    for j = 1:length(imtime)
        fprintf('Extracting %s %d/%d: %s\n', awsname, j, length(imtime), awsdata.imtime(j));
        awsdata.airtemp(j) = griddata(X, Y, imdata(:,:,j), aws.lon, aws.lat, 'linear');
    end
    % Save the data
    writetable(awsdata, fullfile(csvfolder, 'aws_airtemp_era5land.csv'), ...
        'WriteVariableNames', false, 'WriteMode', 'append');
end

awsname = "Zackenberg_M4";
aws = awslist(awslist.awsname == awsname, :);

% find all the nc files
imfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA\untar\ZA30m";
imfiles = dir(fullfile(imfolder, '**', 't2m_elvcorr*.nc'));

for i = 1:length(imfiles)
    imfile = fullfile(imfiles(i).folder, imfiles(i).name);
    fprintf('%d: %s\n', i, imfiles(i).name);
    % Read the full t2m data
    imdata = ncread(imfile, 't2m');
    % Extract the dimensions we want (keeping dimension 3 at index 1)
    imdata = squeeze(imdata(:,:,1,:));
    % Get coordinate information
    X = ncread(imfile, 'X');
    Y = ncread(imfile, 'Y');
    imtime = ncread(imfile, 'time');
    
    % create a table to store time series of extracted data
    awsdata = table('Size', [length(imtime), 3], 'VariableTypes', {'string', 'datetime', 'double'}, 'VariableNames', {'awsname', 'imtime', 'airtemp'});
    awsdata.awsname = repmat(awsname, length(imtime), 1);
    awsdata.imtime = datetime(1850,1,1) + days(imtime);

    % Extract data for all time points at once using interpolation
    for j = 1:length(imtime)
        fprintf('Extracting %s %d/%d: %s\n', awsname, j, length(imtime), awsdata.imtime(j));
        awsdata.airtemp(j) = griddata(X, Y, imdata(:,:,j), aws.lon, aws.lat, 'linear');
    end
    % Save the data
    writetable(awsdata, fullfile(csvfolder, 'aws_airtemp_era5land.csv'), ...
        'WriteVariableNames', false, 'WriteMode', 'append');
end