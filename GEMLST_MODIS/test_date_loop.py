import ee
import numpy as np
ee.Initialize()

months = np.arange(1, 13, 1)
date_start_initial = ee.Date('2001-01-01')

for s in months:

    adv=int(s-1)
    date_start = ee.Date(date_start_initial.advance(adv, 'month'))
    date_end = ee.Date(date_start.advance(1, 'month'))
    print(f'Processing month {s}: from {date_start.format("YYYY-MM-dd").getInfo()} to {date_end.format("YYYY-MM-dd").getInfo()}')

# %%

    def test_do_this(bla):
        print (f'Doing this for month {bla}')
    
    test_do_this(s)
