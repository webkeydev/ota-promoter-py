import gc
import os

from otapromoter import util

try:
    import urequests as requests
    import ujson as json
except:
    import requests
    import json


class OTAException(Exception):
    pass


class PromotedInfo(object):
    def __init__(self, local_files, version, promoted_files):
        self.local_files = local_files
        self.version = version
        self.promoted_files = promoted_files

    def deprecated_files(self):
        deleted_files = []
        for key, value in self.local_files.items():
            if key not in self.promoted_files:
                deleted_files.append(key)
        return deleted_files

    def changed_files(self):
        changed = {}
        for hash, file in self.promoted_files.items():
            if hash not in self.local_files:
                changed[hash] = file

        return changed


class OTAPromoter(object):
    __local_files = {}

    def __init__(self, server='http://127.0.0.1:9090', main_dir='/', next_dir='/update'):
        self.__server_address = server
        self.__main_dir = main_dir
        self.__next_dir = next_dir
        self.__read_current_version()
        self.__promoted_info = None

    def check_and_update(self):
        print("check update...")
        if not self.__check_update():
            return False

        print("new version available")

        self.__create_temp_folder()

        self.__load_hashes()

        # todo handle network issues
        print("download list of promoted files")
        self.__promoted_info = self.__download_promotion_info()

        print("download changed files")
        self.__download_changed_files()

        print("delete deprecated files")
        self.__delete_deprecated_files()

        print("write out version info")
        self.__save_hashes_of_files()
        self.__write_out_version_file()

        print("setup updates")
        self.__move_finale_place()

        print("delete temp folder")
        util.rm_dirs(self.__next_dir)
        return True

    def __check_update(self):
        print("my version: {}".format(self.__version))
        return self.__version != self.__get_remote_version()

    def __get_remote_version(self):
        response = requests.get(self.__get_url("/files/version"))
        if response.status_code != 200:
            raise OTAException(response.text)
        resp = json.loads(response.text)
        return resp["version"]
    
    def __read_current_version(self):
        try:
            p = util.path_join(self.__main_dir, ".version")
            with open(p, 'r') as f:
                self.__version = f.readline().strip()
        except:
            self.__version = 0

    def __load_hashes(self):
        try:
            p = util.path_join(self.__main_dir, ".files")
            with open(p, 'r') as f:
                for line in f:
                    hash, path = line.split(' ', 1 )
                    self.__local_files[hash] = path.strip()
        except Exception as e:
            self.__local_files = {}

    def __download_new_promotion_list(self):
        response = requests.get(self.__get_url("/files"))
        if response.status_code != 200:
            raise OTAException(response.text)
        resp = json.loads(response.text)

        files = {}
        for i in resp['files']:
            files[i['checksum']] = i['path']
        return resp['version'], files

    def __create_temp_folder(self):
        util.rm_dirs(self.__next_dir)
        os.mkdir(self.__next_dir)

    def __download_promotion_info(self):
        version, promoted_files = self.__download_new_promotion_list()
        return PromotedInfo(self.__local_files, version, promoted_files, )

    def __download_by_hash(self, checksum, dst_path):
        print("download: {}".format(dst_path))
        path = "/file/"+checksum
        with open(dst_path, 'w') as dst:
            try:
                response = requests.get(self.__get_url(path))
                if response.status_code != 200:
                    raise OTAException(response.text)
                dst.write(response.text)
            finally:
                response.close()
                dst.close()
                gc.collect()

    def __save_hashes_of_files(self):
        p = util.path_join(self.__next_dir, ".files")
        out = open(p, "a")
        for h, f in self.__promoted_info.promoted_files.items():
            out.write(h+" "+f+'\n')
        out.close()

    def __write_out_version_file(self):
        version_file = util.path_join(self.__next_dir, ".version")
        f = open(version_file, "w")
        f.write(self.__promoted_info.version)
        f.close()

    def __delete_deprecated_files(self):
        for hash in self.__promoted_info.deprecated_files():
            full_path = util.path_join(self.__main_dir, self.__local_files[hash])
            try:
                os.remove(full_path)
            except FileNotFoundError:
                pass

    def __move_finale_place(self):
        for dirs, files in util.walk(self.__next_dir):
            for file in files:
                rel_file = file.split(self.__next_dir + "/", 2)[1]
                dst = util.path_join(self.__main_dir, rel_file)
                directory = util.dir_name(dst)
                if not util.exists(directory):
                    os.mkdir(directory)
                os.rename(file, dst)

    def __download_changed_files(self):
        for hash, path in self.__promoted_info.changed_files().items():
            dst = util.path_join(self.__next_dir, path)
            self.__create_tmp_dir_for_file(dst)
            self.__download_by_hash(hash, dst)

    @staticmethod
    def __create_tmp_dir_for_file(dst):
        directory = util.dir_name(dst)
        if not util.exists(directory):
            util.makedirs(directory)

    def __get_url(self, path):
        return self.__server_address + path
