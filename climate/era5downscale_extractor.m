era5path = "I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\ERA5\JAXA\t2m_elvcorr_2024_daily.nc";
era5info = ncinfo(era5path);

for i = 1:era5info.Variables(1).Size
    t2m = ncread(era5path,'t2m',[1 1 1 i],[Inf Inf 1 1]);
    t2m_1d = t2m(:);

    Y = ncread(era5path,'Y');
    X = ncread(era5path,'X');
    
    % Write to CSV, appending if the file exists
    if i == 1
        writetable('t2m_all.csv', t2m_1d, 'w'); % Create the file on the first iteration
    else
        writetable('t2m_all.csv', t2m_1d, 'a'); % Append on subsequent iterations
    end
end

info = georasterinfo("I:\SCIENCE-IGN-ALL\AVOCA_Group\2_Shared_folders\1_Data\5_GEMLST\v1_02\GEMLST_Landsat\Zackenberg\GEMLST_Landsat_2013-08-21.tif");
info = georasterinfo("I:\SCIENCE-IGN-ALL\AVOCA_Group\1_Personal_folders\3_Shunan\Landsat_LST\data\CARRA\CARRA_skintemp.grib");