from pvlib import pvsystem, modelchain, location

# get the different device (inklusive advanced data) which are tested from SandiaMod
sandia_modules = pvsystem.retrieve_sam('SandiaMod')

# create a txt file that lists all in SandiaMod available pv panels.
with open('solar_brands_overview.txt', 'w') as f:
    f.write(f"{'Module Name':<50}\n")
    f.write("-" * 100 + "\n")

    # write the names of available pv-panels inside the txt-file
    for name in sandia_modules.columns:
        f.write(f"{name[:49]:<50}\n")

brands = ['Canadian_Solar', 'Sharp', 'Panasonic', 'Suntech']

# create a txt files that shows all in SandiaMod available solar panels an advanced states (MaxP, Vmpo, Impo, Eff)
with open('solar_catalog.txt', "w") as f:
    f.write(f"{'Module Name':<50} |  {'Max_P(W)':<8} | {'Vmpo(V)':<8} | {'Impo(A)':<8} | {'Eff(%)':<8}\n")
    f.write("-" * 100 + "\n")
    for name in sandia_modules.columns:
        if any(brand in name for brand in brands):
            specs = sandia_modules[name]  # specifications

    # I think the intendation is wrong after copiying it to this file

    # Calculate Max Power out  (Pm = Vmp * Imp)
    p_max = specs['Vmpo'] * specs['Impo']

    # Compute the Efficiency (Power Out / Power In):
    # Standard light is 1000 W/m², Power In = Area[m²]*1000[W/m²]
    # effective area reduces the shape to the area that is covered with silicon (75-80 [%]) (therefore just this area counts for our analysis)
    area = specs['Area'] * 0.75
    effeciency = p_max / (area * 1e3) * 1e2 if area > 0 else 0

    # write to file with spacing
    f.write(f"{name[:48]:<50} | {p_max:<8.2f} | {specs['Vmpo']:<8.2f} | {specs['Impo']:<8.2f}| {effeciency:<8.2f}%\n")
