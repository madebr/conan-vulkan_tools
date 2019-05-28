# -*- coding: utf-8 -*-

from conanfile_base import ConanfileBase
import shutil
import os


class Conanfile(ConanfileBase):
    name = "vulkan_tools"
    version = ConanfileBase.version
    exports = ConanfileBase.exports + ["conanfile_base.py"]

    settings = "os", "arch", "compiler", "build_type"

    _installer = False

    def package(self):
        super(Conanfile, self).package()
        bindir = os.path.join(self.package_folder, "bin")
        if os.path.isdir(bindir):
            shutil.rmtree(bindir)

    def package_info(self):
        layer_manifest_path = os.path.join(self.package_folder, "share", "vulkan", "explicit_layer.d")
        self.user_info.LAYER_MANIFEST_PATH = layer_manifest_path

        self.output.info("Appending VK_LAYER_PATH environment variable: {}".format(layer_manifest_path))
        self.env_info.VK_LAYER_PATH.append(layer_manifest_path)
