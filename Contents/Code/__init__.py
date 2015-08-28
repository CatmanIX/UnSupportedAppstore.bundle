import os, time, random

####################################################################################################

PREFIX = "/video/unsupportedappstore"

NAME = 'UnSupported AppStore'

ART         = 'art-default.jpg'
ICON        = 'icon-default.png'
PREFS_ICON  = 'icon-prefs.png'

PLUGINS     = 'plugin_details.json'

DEV_MODE    = False

####################################################################################################

def Start():

    HTTP.CacheTime = 0
    
    DirectoryObject.thumb = R(ICON)
    ObjectContainer.art = R(ART)
    
    #Check the list of installed plugins
    if Dict['Installed'] == None:
        Dict['Installed'] = {'UnSupported Appstore' : {'lastUpdate': 'None', 'updateAvailable': 'False', 'installed': 'True'}}
    else:
        if not Dict['Installed']['UnSupported Appstore']['installed']:
            Dict['Installed']['UnSupported Appstore']['installed'] = True
    
    try: version = Dict['Installed']['UnSupported Appstore']['version']
    except: version = 'unknown'
    Logger('UnSupported Appstore version: %s' % version, force=True)
    Logger('Platform: %s %s' % (Platform.OS, Platform.OSVersion), force=True)
    Logger('Server: PMS %s' % Platform.ServerVersion, force=True) 
    
    Logger(Dict['Installed'])
        
    Logger('Plex support files are at ' + Core.app_support_path)
    Logger('Plug-in bundles are located in ' + Core.storage.join_path(Core.app_support_path, Core.config.bundles_dir_name))
    Logger('Plug-in support files are located in ' + Core.storage.join_path(Core.app_support_path, Core.config.plugin_support_dir_name))
    
    updater_running = False
    
    if Prefs['auto-update']:
        if not updater_running:
            updater_running = True
            Thread.Create(BackgroundUpdater)
 
@handler(PREFIX, NAME, "icon-default.png", "art-default.jpg")
def MainMenu():
    
    #Load the list of available plugins
    Dict['plugins'] = LoadData()
    
    oc = ObjectContainer(no_cache=True)
    
    oc.add(DirectoryObject(key=Callback(CheckForUpdates, return_message=True), title="Check for updates"))
    oc.add(DirectoryObject(key=Callback(GenreMenu, genre='New'), title='New'))
    oc.add(DirectoryObject(key=Callback(GenreMenu, genre='All'), title='All'))
    if Prefs['adult']:
        oc.add(DirectoryObject(key=Callback(GenreMenu, genre='Adult'), title='Adult'))
    oc.add(DirectoryObject(key=Callback(GenreMenu, genre='Application'), title='Application'))
    oc.add(DirectoryObject(key=Callback(GenreMenu, genre='Video'), title='Video'))
    oc.add(DirectoryObject(key=Callback(GenreMenu, genre='Pictures'), title='Pictures'))
    oc.add(DirectoryObject(key=Callback(GenreMenu, genre='Metadata Agent'), title='Metadata Agent'))
    oc.add(DirectoryObject(key=Callback(GenreMenu, genre='Music'), title='Music'))
    oc.add(DirectoryObject(key=Callback(InstalledMenu), title='Installed'))
    oc.add(DirectoryObject(key=Callback(UpdateAll), title='Download updates',
        summary="Update all installed plugins.\nThis may take a while."))
    oc.add(PrefsObject(title="Preferences", thumb=R(PREFS_ICON)))

    return oc

@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
    # If Prefs['clear_dict'] is True clear the Dict file and reset the Pref
    if Prefs['clear_dict']:
        Logger("Resetting Dict[]")
        Dict.Reset() # This doesn't seem to work, but new values are set below anyways.
        Dict.Save()
        # Note: Setting lastUpdate to None causes an update to run. Which is probably a good thing if the Dict[] needs to be reset.
        Dict['Installed'] = {'UnSupported Appstore' : {'lastUpdate': 'None', 'updateAvailable': 'False', 'installed': 'True'}}
        Dict['plugins'] = LoadData()
        # Reset Prefs['clear_dict'] to false.
        HTTP.Request('http://localhost:32400/:/plugins/com.plexapp.plugins.unsupportedappstore/prefs/set?clear_dict=False', immediate=True)

@route(PREFIX + '/genre')
def GenreMenu(genre):
    oc = ObjectContainer(title2=genre, no_cache=True)
    plugins = Dict['plugins']
    if genre == 'New':
        for plugin in plugins:
            try:
                plugin['date added'] = Datetime.TimestampFromDatetime(Datetime.ParseDate(plugin['date added']))
            except:
                Log.Exception('Converting date "%s" to timestamp failed' % plugin['date added'])
        date_sorted = sorted(plugins, key=lambda k: k['date added'])
        Logger(date_sorted)
        date_sorted.reverse()
        plugins = date_sorted
    
    for plugin in plugins:
        if plugin['hidden'] == "True": continue ### Don't display plugins which are "hidden"
        else: pass
        if plugin['title'] != "UnSupported Appstore":
            if not Prefs['adult']:
                if "Adult" in plugin['type']:
                    continue
                else:
                    pass
            else:
                pass
            if genre == 'All' or genre == 'New' or genre in plugin['type']:
                if Installed(plugin):
                    if Dict['Installed'][plugin['title']]['updateAvailable'] == "True":
                        subtitle = 'Update available\n'
                    else:
                        subtitle = 'Installed\n'
                else:
                    subtitle = ''
                oc.add(PopupDirectoryObject(key=Callback(PluginMenu, plugin=plugin), title=plugin['title'],
                    summary=subtitle + plugin['description'], thumb=R(plugin['icon'])))
    if len(oc) < 1:
        return ObjectContainer(header=NAME, message='There are no plugins to display in the list: "%s"' % genre)
    return oc

@route(PREFIX + '/installed')
def InstalledMenu():
    oc = ObjectContainer(title2="Installed", no_cache=True)
    plugins = Dict['plugins']
    plugins.sort()
    for plugin in plugins:
        summary = ''
        if Installed(plugin):
            if plugin['hidden'] == "True":
                summary = 'No longer available through the Unsupported Appstore'
            elif Dict['Installed'][plugin['title']]['updateAvailable'] == "True":
                summary = 'Update available'
            else: pass
            oc.add(PopupDirectoryObject(key=Callback(PluginMenu, plugin=plugin), title=plugin['title'],summary=summary,
                thumb=R(plugin['icon'])))
    return oc

@route(PREFIX + '/popup', plugin=dict)
def PluginMenu(plugin):
    oc = ObjectContainer(title2=plugin['title'], no_cache=True)
    if Installed(plugin):
        if Dict['Installed'][plugin['title']]['updateAvailable'] == "True":
            oc.add(DirectoryObject(key=Callback(InstallPlugin, plugin=plugin), title="Update"))
        else:
            oc.add(DirectoryObject(key=Callback(CheckForUpdates, plugin=plugin, return_message=True, install=True), title="Check for Updates"))
        oc.add(DirectoryObject(key=Callback(UnInstallPlugin, plugin=plugin), title="UnInstall"))
    else:
        oc.add(DirectoryObject(key=Callback(InstallPlugin, plugin=plugin), title="Install"))
    return oc
  
@route(PREFIX + '/load')
def LoadData():
    userdata = Resource.Load(PLUGINS)
    return JSON.ObjectFromString(userdata)

@route(PREFIX + '/installedcheck', plugin=dict)
def Installed(plugin):
    try:
        if Dict['Installed'][plugin['title']]['installed'] == "True":
            return True
        else:
            return False
    except:
        ### make sure the Appstore shows up in the list if it doesn't already ###
        if plugin['title'] == 'UnSupported Appstore':
            Dict['Installed'][plugin['title']] = {"installed":"True", "lastUpdate":"None", "updateAvailable":"False"}
            Dict.Save()
        else:
            Dict['Installed'][plugin['title']] = {"installed":"False", "lastUpdate":"None", "updateAvailable":"True"}
            Dict.Save()
        return False
    
    return False

@route(PREFIX + '/installplugin', plugin=dict)
def InstallPlugin(plugin):
    if Installed(plugin):
        errors = Install(plugin)
    else:
        errors = Install(plugin, initial_download=True)
    if errors == 0:
        return ObjectContainer(header=NAME, message='%s installed.' % plugin['title'])
    else:
        if Installed(plugin):
            return ObjectContainer(header=NAME, message="Install of %s failed with %d errors." % (plugin['title'], errors))
        else:
            return ObjectContainer(header=NAME, message="Update of %s failed with %d errors." % (plugin['title'], errors))
    
@route(PREFIX + '/joinpath', plugin=dict)
def JoinBundlePath(plugin, path):
    bundle_path = GetBundlePath(plugin)
    fragments = path.split('/')[1:]

    # Remove the first fragment if it matches the bundle name
    if len(fragments) and fragments[0].lower() == plugin['bundle'].lower():
        fragments = fragments[1:]

    return Core.storage.join_path(bundle_path, *fragments)

@route(PREFIX + '/install', plugin=dict, initial_download=bool)
def Install(plugin, version=None, initial_download=False):
    repo = GetRepo(plugin)
    if initial_download:
        zipPath = plugin['tracking url']
        rssURL = '%s/commits/%s.atom' % (repo, plugin['branch'])
        commits = HTML.ElementFromURL(rssURL)
        version = commits.xpath('//entry')[0].xpath('./id')[0].text.split('/')[-1][:10]
    else:
        zipPath = '%s/archive/%s.zip' % (repo, plugin['branch'])
    Logger('zipPath = ' + zipPath)
    Logger('Downloading from ' + zipPath)
    zipfile = Archive.ZipFromURL(zipPath)

    bundle_path = GetBundlePath(plugin)
    Logger('Extracting to ' + bundle_path)
    
    errors = 0
    init_path = None
    
    for filename in zipfile:
        data = zipfile[filename]

        if not str(filename).endswith('/'):
            if not str(filename.split('/')[-1]).startswith('.'):
                if plugin['title'] == 'UnSupported Appstore' and filename == '__init__.py' and Platform.OS == "Linux":
                    # set the __init__.py file aside and update it after all the others are done
                    init_path = filename
                else:
                    path = JoinBundlePath(plugin, filename)

                    Logger('Extracting file' + path)
                    try:
                        Core.storage.save(path, data)
                    except Exception, e:
                        Logger("Unexpected Error", True)
                        Logger(e, True)
                        errors += 1
            else:
                Logger('Skipping "hidden" file: ' + filename)
        else:
            Logger(filename.split('/')[-2])

            if not str(filename.split('/')[-2]).startswith('.'):
                path = JoinBundlePath(plugin, filename)

                Logger('Extracting folder ' + path)
                Core.storage.ensure_dirs(path)
                
    # Replace the UAS __init__.py last to avoid crippling the plugin on some systems
    if init_path:
        # extract the file under a different name then replace the existing file to avoid wiping the file and breaking the UAS on linux systems
        temp_filename = init_path + '.tmp'
        path = JoinBundlePath(plugin, init_path)
        temp_path = JoinBundlePath(plugin, temp_filename)

        Logger('Extracting file %s as %s' % (init_path, temp_path))
        try:
            Core.storage.save(temp_path, data)
            Core.storage.rename(temp_path, path)
        except Exception, e:
            Logger("Unexpected Error", True)
            Logger(e, True)
            errors += 1
    
    if errors == 0:
        # mark the plugin as updated
        MarkUpdated(plugin['title'], version=version)
        # "touch" the bundle to update the timestamp
        os.utime(bundle_path, None)
    else:
        if initial_download:
            Logger("Install of %s failed with %d errors." % (plugin['title'], errors), force=True)
            # avoid a nasty updater loop and don't restart the 
            return errors
        else:
            Logger("Update of %s failed with %d errors." % (plugin['title'], errors), force=True)
            return errors
    # To help installs/updates register without rebooting PMS...
    # reload the system service if installing a new plugin
    if initial_download:
        try:
            HTTP.Request('http://127.0.0.1:32400/:/plugins/com.plexapp.system/restart', immediate=True)
        except:
            Log("Unable to restart System.bundle. Channel may not show up without PMS restart.")
    # or, if just applying an update, restart the updated plugin
    else:
        try:
            HTTP.Request('http://127.0.0.1:32400/:/plugins/%s/restart' % plugin['identifier'], cacheTime=0, immediate=True)
        except:
            HTTP.Request('http://127.0.0.1:32400/:/plugins/com.plexapp.system/restart', immediate=True)
    return errors

@route(PREFIX + '/updateall')
def UpdateAll():
    errors_total = 0
    for plugin in Dict['plugins']:
        if Dict['Installed'][plugin['title']]['installed'] == "True":
            if Dict['Installed'][plugin['title']]['updateAvailable'] == "False":
                Logger('%s is already up to date.' % plugin['title'])
            else:
                Logger('%s is installed. Downloading updates:' % (plugin['title']))
                errors = Install(plugin)
                if errors == 0:
                    Logger("%s updated." % plugin['title'])
                else:
                    Logger("Update of %s failed with %d errors." % (plugin['title'], errors), force=True)
                    errors_total += errors
        else:
            Logger('%s is not installed.' % plugin['title'])
            pass

    if errors_total == 0:
        return ObjectContainer(header=NAME, message='Updates have been applied.')
    else:
        return ObjectContainer(header=NAME, message='Updates have been applied but there were errors. Check logs for details.')

@route(PREFIX + '/uninstall', plugin=dict)
def UnInstallPlugin(plugin):
    Logger('Uninstalling %s' % GetBundlePath(plugin), force=True)
    # Generate and set a key to use to verify DeleteFile and DeleteFolder were called from within this plugin.
    code = genCode()
    Dict['deleteCode'] = code
    try:
        DeleteFolder(GetBundlePath(plugin), code)
    except:
        Logger("Failed to remove all the bundle's files but we'll mark it uninstalled anyway.")
    if Prefs['delete_data']:
        try:
            try: DeleteFile(GetSupportPath('Preferences', plugin), code)
            except: Logger("Failed to remove Preferences.")
            try: DeleteFolder(GetSupportPath('Data', plugin), code)
            except: Logger("Failed to remove Data.")
            try: DeleteFolder(GetSupportPath('Caches', plugin), code)
            except: Logger("Failed to remove Caches.")
        except:
            Logger("Failed to remove support files. Attempting to uninstall plugin anyway.")

    Dict['Installed'][plugin['title']]['installed'] = "False"
    Dict['Installed'][plugin['title']]['version'] = None
    Dict['deleteCode'] = '' # Clear the key
    Dict.Save()
    try:
        Logger("Attempting to restart the system bundle to force changes to register.", force=True)
        HTTP.Request('http://127.0.0.1:32400/:/plugins/com.plexapp.system/restart', immediate=True)
    except:
        pass
    return ObjectContainer(header=NAME, message='%s uninstalled.' % plugin['title'])

@route(PREFIX + '/deletefile')
def DeleteFile(filePath, code):
    # Verify we were given a good key
    if code != Dict['deleteCode']: Logger("DeleteFile received incorrect code"); return
    Logger('Removing ' + filePath)
    os.remove(filePath)
    return

@route(PREFIX + '/deletefolder')
def DeleteFolder(folderPath, code):
    # Verify we were given a good key
    if code != Dict['deleteCode']: Logger("DeleteFolder received incorrect code"); return
    Logger('Attempting to delete %s' % folderPath)
    if os.path.exists(folderPath):
        for file in os.listdir(folderPath):
            path = Core.storage.join_path(folderPath, file)
            # If the path is a file then call DeleteFile or if it is a path call DeleteFolder.
            # try/execpt here to not stop the whole operation if the delete fails.
            if os.path.isfile(path):
                Logger('Removing ' + path)
                try: DeleteFile(path, code)
                except: Logger('Failed to remove ' + path)
            elif os.path.isdir(path):
                Logger('Removing ' + path)
                try: DeleteFolder(path, code)
                except: Logger('Failed to remove ' + path)
            else:
                Logger('Do not know what to do with ' + path)
        try:
            Logger('Removing ' + folderPath)
            os.rmdir(folderPath)
        except: Logger('Failed to remove ' + folderPath); explode
    else:
        Logger("%s does not exist so we don't need to remove it" % folderPath)
    return

@route(PREFIX + '/genCode')
def genCode(length=20):
    # Generate and return a random alphanumeric key.
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    code = ''.join(random.choice(chars) for x in range(length))
    return code

@route(PREFIX + '/updatecheck', plugin=dict)
def CheckForUpdates(install=False, return_message=False, plugin=None):
    #use the github commit feed for each installed plugin to check for available updates
    if plugin:
        if plugin['hidden'] == "true":
            return ObjectContainer(header="Unsupported Appstore", message="%s : No longer supported. No updates." % plugin['title'])
        GetRSSFeed(plugin=plugin, install=install)
        if return_message:
            return ObjectContainer(header="Unsupported Appstore", message="%s : Up-to-date" % plugin['title'])
    else:
        @parallelize
        def GetUpdateList():
            for num in range(len(Dict['plugins'])):
                @task
                def ParallelUpdater(num=num):
                    plugin = Dict['plugins'][num]
                    if Installed(plugin):
                        GetRSSFeed(plugin=plugin, install=install)
        if return_message:
            return ObjectContainer(header="Unsupported Appstore", message="Update check complete.")
        else:
            return

@route(PREFIX + '/GetFeed', plugin=dict)
def GetRSSFeed(plugin, install=False):
    repo = GetRepo(plugin)
    rssURL = '%s/commits/%s.atom' % (repo, plugin['branch'])
    commits = HTML.ElementFromURL(rssURL)
    mostRecent = Datetime.ParseDate(commits.xpath('//entry')[0].xpath('./updated')[0].text[:-6])
    commitHash = commits.xpath('//entry')[0].xpath('./id')[0].text.split('/')[-1][:10]
    if Dict['Installed'][plugin['title']]['lastUpdate'] == "None":
        Dict['Installed'][plugin['title']]['updateAvailable'] = "True"
    elif mostRecent > Dict['Installed'][plugin['title']]['lastUpdate']:
        Dict['Installed'][plugin['title']]['updateAvailable'] = "True"
    else:
        Dict['Installed'][plugin['title']]['updateAvailable'] = "False"
        # start adding version hashes to already installed plugins by checking if the key exists
        if 'version' not in Dict['Installed'][plugin['title']]:
            Dict['Installed'][plugin['title']]['version'] = commitHash
        else:
            version = Dict['Installed'][plugin['title']]['version']
            # compared stored version to latest commitHash
            if version != commitHash: #if they don't match better update for good measure
                Dict['Installed'][plugin['title']]['updateAvailable'] = "True"
        

    if Dict['Installed'][plugin['title']]['updateAvailable'] == "True":
        Logger(plugin['title'] + ': Update available', force=True)
        if install:
            if plugin['title'] == 'UnSupported Appstore' and DEV_MODE:
                pass
            else:
                Install(plugin, version=commitHash)
    else:
        Logger(plugin['title'] + ': Up-to-date :: Version %s' % commitHash, force=True)
    
    Dict.Save()
    
    return

@route(PREFIX + '/repo', plugin=dict)
def GetRepo(plugin):
    repo = plugin['repo']
    if repo.startswith("git@github.com"):
        repo = repo.replace('git@github.com:', 'https://github.com/')
    elif repo.startswith("https://github.com/"):
        pass
    else:
        Logger("Error in repo URL format. Please report this https://github.com/mikedm139/UnSupportedAppstore.bundle/issues", force=True)
    
    if repo.endswith(".git"):
        repo = repo.split(".git")[0]
        
    return repo


@route(PREFIX + '/updater')
def BackgroundUpdater():
    if not Dict['plugins']:
        Dict['plugins'] = LoadData()
    while Prefs['auto-update']:
        Logger("Running auto-update.", force=True)
        for plugin in Dict['plugins']:
            if Installed(plugin):
                GetRSSFeed(plugin=plugin, install=True)
        # check for updates every 24hours... give or take 30 minutes to avoid hammering GitHub
        sleep_time = 24*60*60 + (random.randint(-30,30))*60
        hours, minutes = divmod(sleep_time/60, 60)
        Logger("Updater will run again in %d hours and %d minutes" % (hours, minutes), force=True)
        while sleep_time > 0:
            remainder = sleep_time%(3600)
            if  remainder > 0:
                time.sleep(remainder)
                sleep_time = sleep_time - remainder
            Logger("Time until next auto-update = %d hours" % (int(sleep_time)/3600))
            sleep_time = sleep_time - 3600
            time.sleep(3600)
    return
    
@route(PREFIX + '/plugindir')
def GetPluginDirPath():
    return Core.storage.join_path(Core.app_support_path, Core.config.bundles_dir_name)

@route(PREFIX + '/bundlepath', plugin=dict)    
def GetBundlePath(plugin):
    return Core.storage.join_path(GetPluginDirPath(), plugin['bundle'])

@route(PREFIX + '/supportpath', plugin=dict)
def GetSupportPath(directory, plugin):
    if directory == 'Preferences':
        return Core.storage.join_path(Core.app_support_path, Core.config.plugin_support_dir_name, directory, (plugin['identifier'] + '.xml'))
    else:
        return Core.storage.join_path(Core.app_support_path, Core.config.plugin_support_dir_name, directory, plugin['identifier'])

@route(PREFIX + '/logger')
def Logger(message, force=False):
    if DEV_MODE:
        force = True
    if force or Prefs['debug']:
        Log.Debug(message)
    else:
        pass

'''allow plugins to mark themselves updated externally'''
@route('%s/mark-updated/{title}' % PREFIX)
def MarkUpdated(title, version=None):
    Dict['Installed'][title]['installed'] = "True"
    Logger('%s "Installed" set to: %s' % (title, Dict['Installed'][title]['installed']))
    Dict['Installed'][title]['lastUpdate'] = Datetime.Now()
    Logger('%s "LastUpdate" set to: %s' % (title, Dict['Installed'][title]['lastUpdate']))
    Dict['Installed'][title]['updateAvailable'] = "False"
    Logger('%s "updateAvailable" set to: %s' % (title, Dict['Installed'][title]['updateAvailable']))
    if version:
        Dict['Installed'][title]['version'] = version
        Logger('%s "version" set to: %s' % (title, Dict['Installed'][title]['version']))
    Dict.Save()
    return
    
