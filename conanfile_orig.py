# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class LibnameConan(ConanFile):
    name = "vulkan_tools_installer"
    version = "1.1.106.0"
    description = "Tools to aid in Vulkan development including useful layers, trace and replay, and tests"
    topics = ("conan", "vulkan", "tools", "lunarg", )
    url = "https://github.com/bincrafters/conan-vulkan_tools"
    homepage = "https://github.com/LunarG/VulkanTools"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "Apache-2.0"
    exports = ["LICENSE.md", ]
    exports_sources = ["CMakeLists.txt", ]
    generators = "cmake",

    settings = "os_build", "arch_build", "compiler",
    # options = {"shared": [True, False], "fPIC": [True, False]}
    # default_options = {"shared": False, "fPIC": True}

    _source_subfolder = "source_subfolder"

    @property
    def _vulkan_version(self):
        vulkan_version, _ = self.version.rsplit(".", 1)
        return vulkan_version

    def build_requirements(self):
        self.build_requires("vulkan_headers/{}@{}/{}".format(self._vulkan_version, self.user, self.channel))
        self.build_requires("jsoncpp/1.0.0@theirix/stable")

    def requirements(self):
        self.requires("vulkan_loader/{}@{}/{}".format(self._vulkan_version, self.user, self.channel))
        self.requires("vulkan_validation_layers/{}@{}/{}".format(self._vulkan_version, self.user, self.channel))

    def system_requirements(self):
        if tools.os_info.with_apt or tools.os_info.with_yum:
            if tools.os_info.with_apt:
                xcb_extra_pkgs = ["libxcb-keysyms1-dev", "libxcb-ewmh-dev", ]
                arch_lookup = {
                    "x86_64": "amd64",
                    "x86": "i386",
                }
                pack_sep = ":"
            elif tools.os_info.with_yum:
                xcb_extra_pkgs = ["xcb-util-keysyms-devel", "xcb-util-wm-devel", ]
                arch_lookup = {
                    "x86_64": "x86_64",
                    "x86": "i686",
                }
                pack_sep = "."
            packages = []
            if self._safe_vulkan_loader_option("xcb"):
                packages.extend(xcb_extra_pkgs)
            installer = tools.SystemPackageTool()
            arch = arch_lookup.get(str(self.settings.arch_build), str(self.settings.arch_build))
            for package in packages:
                installer.install("{}{}{}".format(package, pack_sep, arch))

    def source(self):
        source_url = "https://github.com/LunarG/VulkanTools/archive/sdk-{}.tar.gz".format(self.version)
        sha256 = "b0975fd000c77146b1d79aed5d1becf428718a67ab40e224f4c6fc2c65714b71"
        tools.get(source_url, sha256=sha256)
        os.rename("VulkanTools-sdk-{}".format(self.version), self._source_subfolder)

        def remove_jsoncpp_sources(subfolder):
            cmakelists = os.path.join(self._source_subfolder, subfolder, "CMakeLists.txt")
            tools.replace_in_file(cmakelists ,"${JSONCPP_SOURCE_DIR}/jsoncpp.cpp", "")
            tools.replace_in_file(cmakelists , "${JSONCPP_INCLUDE_DIR}", "")
            return cmakelists
        via_cmakelists = remove_jsoncpp_sources("via")
        tools.replace_in_file(via_cmakelists,
                              "target_link_libraries(vkvia Vulkan::Vulkan)",
                              "target_link_libraries(vkvia Vulkan::Vulkan CONAN_PKG::jsoncpp)")

        layersvt_cmakelists = remove_jsoncpp_sources("layersvt")
        tools.replace_in_file(layersvt_cmakelists,
                              "target_link_Libraries(VkLayer_${target} ${VkLayer_utils_LIBRARY})",
                              "target_link_Libraries(VkLayer_${target} ${VkLayer_utils_LIBRARY} CONAN_PKG::jsoncpp)")
        tools.replace_in_file(os.path.join(self._source_subfolder, "layersvt", "device_simulation.cpp"),
                              "#include <json/json.h>",
                              "#include <json/json.h>\n"
                              "#include <json/version.h>")

    def _safe_vulkan_loader_option(self, option):
        if option in self.options["vulkan_loader"].fields:
            return getattr(self.options["vulkan_loader"], option)
        return False

    def build(self):
        try:
            os.mkdir("vktrace")
        except FileExistsError:
            pass
        cmake = CMake(self)
        cmake_defines = {
            "WITH_HARDENING": True,
            "CONAN_BUILD_TYPE": "Release",
            "BUILD_TESTS": False,
            "BUILD_LAYERSVT": True, #lib
            "BUILD_VLF": True, #lib: layersfactory

            "BUILD_VKTRACE": True,#lib: vktrace_layer; exe: vktrace+vkreplay+vktracedump+vktraceviewer
            "BUILD_VKTRACEVIEWER": True, #exe: vktraceviewer
            "BUILD_VKTRACE_LAYER": True, #lib: vktrace_layer
            "BUILD_VKTRACE_REPLAY": self.options.xcb or self.options.wayland,  # exe: vkreplay

            "BUILD_VIA": True, #exe: vkvia
            "BUILD_LAYERMGR": True, #exe: vkconfig

            "VULKAN_HEADERS_INSTALL_DIR": self.deps_cpp_info["vulkan_headers"].rootpath,
            "VULKAN_LOADER_INSTALL_DIR": self.deps_cpp_info["vulkan_loader"].rootpath,
            "VULKAN_VALIDATIONLAYERS_INSTALL_DIR": self.deps_cpp_info["vulkan_validation_layers"].rootpath,
            "BUILD_WSI_WAYLAND_SUPPORT": self._safe_vulkan_loader_option("wayland"),
            "BUILD_WSI_XCB_SUPPORT": self._safe_vulkan_loader_option("xcb"),
            "BUILD_WSI_XLIB_SUPPORT": self._safe_vulkan_loader_option("xlib"),
        }
        cmake.configure(defs=cmake_defines)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)
