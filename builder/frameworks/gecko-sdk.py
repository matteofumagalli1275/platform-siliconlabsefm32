# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from glob import glob
from os.path import basename, isdir, isfile, join
from shutil import copy
from string import Template
import sys

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()

FRAMEWORK_DIR = platform.get_package_dir("framework-gecko-sdk")
assert isdir(FRAMEWORK_DIR)

FRAMEWORK_CORE = env.BoardConfig().get("build.mcu")[5:7].lower()
MCU_FAMILY = env.BoardConfig().get("build.mcu")[0:7]

STARTUP_FILE_EXCEPTIONS = {}


def get_startup_file(mcu):

    startup_file = join(
        FRAMEWORK_DIR, "platform", "Device", "SiliconLabs",
         mcu.upper(), "Source", "GCC", "startup_" + mcu.lower() + ".S"
    )

    if mcu in STARTUP_FILE_EXCEPTIONS:
        return STARTUP_FILE_EXCEPTIONS[mcu]


    if not startup_file:
        sys.stderr.write(
            """Error: There is no default startup file for %s MCU!
            Please add initialization code to your project manually!""" % mcu)
        env.Exit(1)
    return basename(startup_file[0])


def get_linker_script(mcu):
    ldscript = join(
        FRAMEWORK_DIR, "platform", "Device", "SiliconLabs",
         mcu.upper(), "Source", "GCC",mcu.lower() + ".ld"
    )

    if isfile(ldscript):
        return ldscript

	print("Error! Cannot find a linker script for the required board! "
		  "Firmware will be linked with a default linker script!")
			  
    return default_ldscript


env.Replace(
    AS="$CC", ASCOM="$ASPPCOM",
    LDSCRIPT_PATH=get_linker_script(env.BoardConfig().get("build.mcu")),
    LINKFLAGS=[
        "-g",
        #"gdwarf-2",
        "-mthumb",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu")#,
		#"-Xlinker -no-enum-size-warning -Xlinker -no-wchar-size-warning -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    ]
)

env.ProcessFlags("-DSILABS_AF_USE_HWCONF=1 -D__NO_SYSTEM_INIT=1 -DEFR32BG1B232F256GM48=1")

# restore external build flags
if "build.extra_flags" in env.BoardConfig():
    env.ProcessFlags(env.BoardConfig().get("build.extra_flags"))
# remove base flags
env.ProcessUnFlags(env.get("BUILD_UNFLAGS"))
# apply user flags
env.ProcessFlags(env.get("BUILD_FLAGS"))

env.Append(
    CPPPATH=[
        join(FRAMEWORK_DIR, "hardware", "kit", "common", "bsp"),
		join(FRAMEWORK_DIR, "hardware", "kit", "common", "drivers"),
		join(FRAMEWORK_DIR, "hardware", "kit", "EFR32BG1_BRD4300C", "config"),
		join(FRAMEWORK_DIR, "platform", "bootloader", "api"),
		join(FRAMEWORK_DIR, "platform", "CMSIS", "include"),
		join(FRAMEWORK_DIR, "platform", "Device", "include"),
		join(FRAMEWORK_DIR, "platform", "Device", "SiliconLabs", "EFR32BG1B", "Include"),
        join(FRAMEWORK_DIR, "platform", "Drivers", "CMSIS", "SiliconLabs", "EFR32BG1B", "Include"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "common", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "dmadrv", "config"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "dmadrv", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "gpiointerrupt", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "nvm", "config"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "nvm", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "rtcdrv", "config"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "rtcdrv", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "sleep", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "spidrv", "config"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "spidrv", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "tempdrv", "config"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "tempdrv", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "uartdrv", "config"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "uartdrv", "inc"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "ustimer", "config"),
		join(FRAMEWORK_DIR, "platform", "emdrv", "ustimer", "inc"),
		join(FRAMEWORK_DIR, "platform", "emlib", "inc"),
		join(FRAMEWORK_DIR, "platform", "radio", "rail_lib", "chip", "efr32"),
		join(FRAMEWORK_DIR, "platform", "radio", "rail_lib", "chip", "efr32", "rf", "common", "cortex"),
		join(FRAMEWORK_DIR, "platform", "radio", "rail_lib", "common"),
		join(FRAMEWORK_DIR, "protocol", "bluetooth_2.4", "ble_stack", "inc", "common"),
		join(FRAMEWORK_DIR, "protocol", "bluetooth_2.4", "ble_stack", "inc", "soc"),
    ],
    LIBPATH=[
        join(FRAMEWORK_DIR, "platform", "CMSIS", "Lib", "GCC")
		#,
        #join(FRAMEWORK_DIR, "platformio", "ldscripts")
    ]
)

#
# Target: Build HAL Library
#

libs = []

libs.append(join(FRAMEWORK_DIR, "protocol", "bluetooth_2.4", "lib", "EFR32BG1B", "EABI","stack.a"))
libs.append(join(FRAMEWORK_DIR, "protocol", "bluetooth_2.4", "lib", "EFR32BG1B", "EABI","binstack.o"))
libs.append(join(FRAMEWORK_DIR, "protocol", "bluetooth_2.4", "lib", "EFR32BG1B", "GCC","bgapi.a"))
libs.append(join(FRAMEWORK_DIR, "protocol", "bluetooth_2.4", "lib", "EFR32BG1B", "EABI","binbootloader.o"))

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "platform", "emdrv", "build"),
    join(FRAMEWORK_DIR, "platform", "dmadrv", "src"),
    src_filter="+<*.c>"
))

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "platform", "emlib", "build"),
    join(FRAMEWORK_DIR, "platform", "emlib", "src"),
	src_filter="+<*.c>"
))


env.Append(LIBS=libs)
