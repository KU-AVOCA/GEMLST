%%
clearvars
tic
imfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\data\GEMLST_MODIS\ERA5\GL500m\t2m";
imoutfolder = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\data\GEMLST_MODIS\ERA5\GL500m\preview";
imfiles = dir(fullfile(imfolder, '**', 't2m_elvcorr*.nc'));

%% 
for i = 1:length(imfiles)
    imfile = fullfile(imfiles(i).folder, imfiles(i).name);
    fprintf('%d: %s\n', i, imfiles(i).name);
    % Read the full t2m data
    imdata = ncread(imfile, 't2m') - 273.15;
    X = ncread(imfile, 'X');
    Y = ncread(imfile, 'Y');
    imtime = ncread(imfile, 'time');
    imtime = datetime(1850,1,1) + days(imtime);

    fig = figure('Visible', 'off', 'Position', [100, 100, 800, 800]);
    mapshow(X, Y, imdata, 'DisplayType', 'surface');
    colormap(cmocean('thermal'));
    clim([-30 30]);
    cb = colorbar('location', 'eastoutside');
    title(string(imtime));
    exportgraphics(fig, fullfile(imoutfolder, string(imtime) + '.png'), "Resolution",300);    
    close(fig);
end

elapsed_time = toc;
fprintf('Done! Elapsed time is %s\n', string(duration(seconds(elapsed_time),'Format','hh:mm:ss')));

clearvars