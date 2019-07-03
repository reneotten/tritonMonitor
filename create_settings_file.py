import json

settings=dict()

settings['log_file'] = r"\\134.61.7.160\LogFiles\60555 Bluhm\log 190609 120150.vcl"

settings['colors'] = {
    'background': '#333333',
    'text': '#7FDBFF'
}
    
settings['external_stylesheets'] = ['./static/bWLwgP.css']

settings['layout'] = {
                'plot_bgcolor': settings['colors']['background'],
                'paper_bgcolor': settings['colors']['background'],                
                'font': {
                    'color': settings['colors']['text']
                },
                'uirevision': None,
                'height': 800
            }

settings['lakeshore_sensors']=[
                'PT1 Head', 
                'PT1 Plate', 
                'PT2 Head', 
                'PT2 Plate', 
                'Magnet', 
                'Still Plate',
                'Cold Plate', 
                'MC Plate',
                'MC Plate Cernox'
                ]

settings['pressure_sensors']=[
                'P1 Tank (Bar)',
                'P2 Condense (Bar)',
                'P3 Still (mBar)',
                'P4 TurboBack (mBar)',
                'P5 ForepumpBack (Bar)',
                'Dewar (mBar)' #Does it make sense to include the dewar or move it to misc?
                ]

settings['misc_sensors']=[
            'Input Water Temp', 
            'Output Water Temp' ,
            'Oil Temp', 
            'Helium Temp', 
            'Motor Current', 
            'Low Pressure', 
            'Low Pressure Avg', 
            'Still heater (W)',
            'chamber heater (W)', 
            'IVC sorb heater (W)', 
            'turbo current(A)', 
            'turbo power(W)', 
            'turbo speed(Hz)', 
            'turbo motor(C)', 
            'turbo bottom(C)'
            ]

with open('triton200.json','w') as file:
    json.dump(settings,file, indent=4, sort_keys=True)