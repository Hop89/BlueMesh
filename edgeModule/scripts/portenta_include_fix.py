Import("env")

if env.get("PIOENV") == "portenta_c33":
    pkg_dir = env.PioPlatform().get_package_dir("framework-arduinorenesas-portenta")
    if pkg_dir:
        env.Append(CPPPATH=[pkg_dir + "/libraries/ESPhost/src"])