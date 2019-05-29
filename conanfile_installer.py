# -*- coding: utf-8 -*-

import os
import shutil
from conanfile_base import ConanfileBase


class ConanfileInstaller(ConanfileBase):
    name = "vulkan_tools_installer"
    version = ConanfileBase.version
    exports = ConanfileBase.exports + ["conanfile_base.py"]

    settings = "os_build", "arch_build", "compiler", "arch"

    _installer = True

    def requirements(self):
        super(ConanfileInstaller, self).requirements()
        self.requires("qt/5.12.3@bincrafters/stable")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.arch

    def package(self):
        super(ConanfileInstaller, self).package()
        libdir = os.path.join(self.package_folder, "lib")
        incdir = os.path.join(self.package_folder, "include")
        if os.path.isdir(libdir):
            shutil.rmtree(libdir)
        if os.path.isdir(incdir):
            shutil.rmtree(incdir)

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info('Appending PATH environment variable: {}'.format(bindir))
        self.env_info.PATH.append(bindir)
