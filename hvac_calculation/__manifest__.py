{
    "name": "HVAC Complete Solution",
    "version": "19.0.3.0.0",
    "category": "Sales/Engineering",
    "summary": "Complete HVAC: Heating, Cooling, Hot Water & Pool",
    "description": """
        Complete HVAC Solution Module
        ==============================
        
        THREE MAIN SECTIONS:
        
        🔥 CENTRAL HEATING
        - Heat load calculation
        - Boiler selection
        - Radiator selection (Aluminum, Towel)
        - Under Floor Heating
        - Piping network
        
        ❄️ CENTRAL AIR CONDITIONING
        - Cooling load calculation (W/m² & BTU)
        - Chiller selection
        - AHU selection
        - FCU selection
        - Ductwork calculation
        - Diffuser selection
        
        💧 HOT WATER & POOL HEATING
        - Hot water demand calculation
        - Water heater selection (Gas, Electric, Solar, Heat Pump)
        - Pool heating calculation (by volume & area)
        - Solar panel calculation
        - Pool equipment selection
        
        FEATURES:
        - Auto equipment selection
        - Professional PDF reports
        - Integrated quotations
        - Equipment database
    """,
    "author": "Your Company",
    "website": "https://www.yourcompany.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale",
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        
        # Data - Heating
        "data/heating/hvac_boiler_data.xml",
        "data/heating/hvac_radiator_data.xml",
        "data/heating/hvac_terms_data.xml",
        
        # Data - Cooling
        "data/cooling/hvac_chiller_data.xml",
        "data/cooling/hvac_ahu_data.xml",
        "data/cooling/hvac_fcu_data.xml",
        
        # Data - Hot Water
        "data/hotwater/hvac_water_heater_data.xml",
        "data/hotwater/hvac_pool_heater_data.xml",
        
        # Main Menu and Terms (MUST BE FIRST)
        "views/hvac_terms_views.xml",
        "views/hvac_main_menus.xml",
        
        # Views - Heating
        "views/heating/hvac_boiler_views.xml",
        "views/heating/hvac_radiator_views.xml",
        "views/heating/hvac_heating_piping_views.xml",
        "views/heating/hvac_heating_project_views.xml",
        "views/heating/hvac_heating_menus.xml",
        
        # Views - Cooling
        "views/cooling/hvac_chiller_views.xml",
        "views/cooling/hvac_ahu_views.xml",
        "views/cooling/hvac_fcu_views.xml",
        "views/cooling/hvac_ductwork_views.xml",
        "views/cooling/hvac_cooling_project_views.xml",
        "views/cooling/hvac_cooling_menus.xml",
        
        # Views - Hot Water
        "views/hotwater/hvac_water_heater_views.xml",
        "views/hotwater/hvac_pool_heater_views.xml",
        "views/hotwater/hvac_hotwater_project_views.xml",
        "views/hotwater/hvac_hotwater_menus.xml",
        
        # Reports
        "report/report_heating_project.xml",
        "report/report_cooling_project.xml",
        "report/report_hotwater_project.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
