%% 
tic
filepath = "/data/shunan/data/climate/CARRA.grib";
iminfo = georasterinfo(filepath);

%% Define AWS data as a MATLAB structure array
% Initialize struct array
% Create table with AWS data
awsname = {'Kobbefjord_M500', 'Disko_T1', 'Disko_T2', 'Disko_T3', 'Disko_T4', 'Disko_AWS2', 'Zackenberg_M2', 'Zackenberg_M3', 'Zackenberg_M4'};
lat = [64.12248229980469, 69.27300262451172, 69.28909301757812, 69.2767105102539, 69.25126647949219, 69.25348663330078, 74.46549224853516, 74.50310516357422, 74.47307586669922];
lon = [-51.37199020385742, -53.479400634765625, -53.43281936645508, -53.45709991455078, -53.49897003173828, -53.514129638671875, -20.563194274902344, -20.459354400634766, -20.552143096923828];

% Create the table
awslist = table(awsname', lat', lon', 'VariableNames', {'awsname', 'lat', 'lon'});

% Add empty columns for time and skintemp
awslist = addvars(awslist, NaT(height(awslist),1), NaN(height(awslist),1), 'NewVariableNames', {'time', 'skintemp'});

%%
metadata = iminfo.Metadata;
numbands = iminfo.NumBands;

for i = 36748:numbands
    fprintf('Processing image %d of %d %s\n', i, numbands, metadata.ReferenceTime(i));

    [A, R] = readgeoraster(filepath, 'Band', i);
    [X, Y] = meshgrid(R.XWorldLimits(1):2500:R.XWorldLimits(2), R.YWorldLimits(2):-2500:R.YWorldLimits(1));
    % mapshow(X, Y, A, 'DisplayType', 'surface');
    [awsX, awsY] = projfwd(R.ProjectedCRS, [awslist.lat], [awslist.lon]);

    % extract data by interpolation
    aws_data = interp2(X, Y, A, awsX, awsY);
    awslist.skintemp = aws_data;
    awslist.time = repmat(metadata.ReferenceTime(i), height(awslist), 1);

    % Define CSV filename
    csv_filename = "/data/shunan/data/climate/carra_aws_data.csv";

    % Check if it's the first iteration to determine whether to write headers
    if i == 1
        % First iteration - write with headers
        writetable(awslist, csv_filename, 'WriteMode', 'overwrite','WriteVariableNames', true);
    else
        % Subsequent iterations - append without headers
        writetable(awslist, csv_filename, 'WriteMode', 'append', 'WriteVariableNames', false);
    end

end

elapsed_time = toc;
fprintf('Elapsed time is %s\n', string(duration(seconds(elapsed_time),'Format','hh:mm:ss')));
