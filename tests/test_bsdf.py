from pyradiance import bsdf

sddata = bsdf.load_file("Resources/t3.xml")

theta = 0
phi = 0

# Direct hemispherical specular transmittance
t_spec = bsdf.direct_hemi(
    sddata, theta, phi, bsdf.SAMPLE_ALL & ~bsdf.SAMPLE_R & ~bsdf.SAMPLE_DF
)
print(f"{t_spec=}")


# Generate 1000 transmission samples
nsamp = 1000
samples = bsdf.sample(sddata, theta, phi, nsamp, bsdf.SAMPLE_ALL & ~bsdf.SAMPLE_R)
print(samples)

# Query an incident and outgoing angle
val = bsdf.query(sddata, theta, phi, 0, 0)
print(val)
