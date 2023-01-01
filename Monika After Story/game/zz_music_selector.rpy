# Module that handles the music selection screen
# we start with zz to ensure this loads LAST
#
# NOTE: We added support for custom music.
# To add custom music to your game:
# 1. Ensure that the custom music is of OGG/VORBIS / MP3 / OPUS format.
# 2. Add a directory "custom_bgm" in your DDLC/ directory.
# 3. Drop your music into that directory.
# 4. Start the game

default persistent._mas_pm_added_custom_bgm = False

# music inits first, so the screen can be made well
init -1 python in songs:
    import os
    import mutagen.mp3 as muta3
    import mutagen.oggopus as mutaopus
    import mutagen.oggvorbis as mutaogg
    import store

    # MUSICAL CONSTANTS
    # SONG NAMES
    PIANO_COVER = "Your Reality (Piano Cover)"
    JUST_MONIKA = "Just Monika"
    YOURE_REAL = "Your Reality"
    STILL_LOVE = "I Still Love You"
    MY_FEELS = "My Feelings"
    MY_CONF = "My Confession"
    OKAY_EV_MON = "Okay, Everyone! (Monika)"
    DDLC_MT_80 = "Doki Doki Theme (80s ver.)"
    SAYO_NARA = "Surprise!"
    SAYO_NARA_SENS = "Sayonara"
    PLAYWITHME_VAR6 = "Play With Me (Variant 6)"
    YR_EUROBEAT = "Your Reality (Eurobeat ver.)"
    MONIKA_LULLABY = "Monika's Lullaby"
    NO_SONG = "No Music"

    # SONG FILEPATHS
    FP_PIANO_COVER = "mod_assets/bgm/runereality.ogg"
    FP_JUST_MONIKA = "bgm/m1.ogg"
    FP_YOURE_REAL = "bgm/credits.ogg"
    FP_STILL_LOVE = "bgm/monika-end.ogg"
    FP_MY_FEELS = "<loop 3.172>bgm/9.ogg"
    FP_MY_CONF =  "<loop 5.861>bgm/10.ogg"
    FP_OKAY_EV_MON = "<loop 4.444>bgm/5_monika.ogg"
    FP_DDLC_MT_80 = (
        "<loop 17.451 to 119.999>mod_assets/bgm/ddlc_maintheme_80s.ogg"
    )
    FP_SAYO_NARA = "<loop 36.782>bgm/d.ogg"
    FP_PLAYWITHME_VAR6 = "<loop 43.572>bgm/6s.ogg"
    FP_YR_EUROBEAT = "<loop 1.414>mod_assets/bgm/eurobeatreality.ogg"
    FP_MONIKA_LULLABY = "<loop 0.01>mod_assets/bgm/Monika's Lullaby.ogg"
    FP_THIRTY_MIN_OF_SILENCE = "<silence 1800.0>"
    FP_NO_SONG = None


    # functions
    def adjustVolume(channel="music",up=True):
        #
        # Adjusts the volume of the given channel by the volume bump value
        #
        # IN:
        #   channel - the channel to adjust volume
        #       (DEFAULT: music)
        #   up - True means increase volume, False means decrease
        #       (DEFAULT: True)
        direct = 1
        if not up:
            direct = -1

        # volume checks
        new_vol = _sanitizeVolume(getUserVolume(channel)+(direct*vol_bump))
        setUserVolume(new_vol, channel)


    def getVolume(channel):
        """
        Gets the volume of the given audio channel.
        NOTE: gets the real volume, not user-defined slider volume.

        IN:
            channel - audio channel to get volume for (string)

        RETURNS: volume of the audio channel as double/float
        """
        return renpy.audio.audio.get_channel(channel).context.secondary_volume


    def getUserVolume(channel):
        """
        Gets user-defined slider volume of the given channel.
        NOTE: this is indepenent of the actual channel volume.
            Using set_volume will NOT affect this.

        IN:
            channel - audio channel to get volume for (string)

        RETURNS: value of the user slider for the audio channel (double/float)
        """
        return renpy.game.preferences.volumes.get(
            renpy.audio.audio.get_channel(channel).mixer,
            0.0
        )


    def hasMusicMuted():
        """
        Checks if the player has the music channel muted or the 'Mute All' option enabled.

        RETURNS: True if the music channel is muted or the 'Mute All' option is enabled, False otherwise
        """
        return renpy.game.preferences.mute["music"] or getUserVolume("music") == 0.0


    def getPlayingMusicName():
        #
        # Gets the name of the currently playing song.
        #
        # IN:
        #   channel - the audio channel to get the playing file
        #
        # RETURNS:
        #   The name of the currently playing song, as defined here in
        #   music_choices, Or None if nothing is currently playing
        #
        # ASSUMES:
        #   music_choices (songs store)
        curr_filename = renpy.music.get_playing()

        # check for brackets (so we can confine the check to filename only)
        if curr_filename:
            bracket_endex = curr_filename.find(">")

            if bracket_endex >= 0:
                curr_filename = curr_filename[bracket_endex:]

            # go through music choices and find the match
            for name,song in music_choices:

                # bracket check
                if song: # None check
                    bracket_endex = song.find(">")

                    if bracket_endex >= 0:
                        check_song = song[bracket_endex:]
                    else:
                        check_song = song
                else:
                    check_song = song

                if curr_filename == check_song:
                    return name
        return None

    def initMusicChoices(sayori=False):
        #
        # Sets up the music choices list
        #
        # IN:
        #   sayori - True if the player name is sayori, which means only
        #       allow Surprise in the player

        global music_choices
        global music_pages
        music_choices = list()
        # SONGS:
        # if you want to add a song, add it to this list as a tuple, where:
        # [0] -> Title of song
        # [1] -> Path to song
        if not sayori:
            music_choices.append((JUST_MONIKA, FP_JUST_MONIKA))
            music_choices.append((YOURE_REAL, FP_YOURE_REAL))

            # Shoutout to Rune0n for this wonderful piano cover!
            music_choices.append((PIANO_COVER, FP_PIANO_COVER))

            # Shoutout to TheAloofPotato for this wonderful eurobeat version!
            music_choices.append((YR_EUROBEAT, FP_YR_EUROBEAT))

            music_choices.append((STILL_LOVE, FP_STILL_LOVE))
            music_choices.append((MY_FEELS, FP_MY_FEELS))
            music_choices.append((MY_CONF, FP_MY_CONF))
            music_choices.append((OKAY_EV_MON, FP_OKAY_EV_MON))
            music_choices.append((PLAYWITHME_VAR6, FP_PLAYWITHME_VAR6))

            # BIG SHOUTOUT to HalHarrison for this lovely track!
            music_choices.append((DDLC_MT_80, FP_DDLC_MT_80))

            # NOTE: this is locked until we can set this up later.
#            music_choices.append((MONIKA_LULLABY, FP_MONIKA_LULLABY))

        # sayori only allows this
        if store.persistent._mas_sensitive_mode:
            sayonara_name = SAYO_NARA_SENS
        else:
            sayonara_name = SAYO_NARA
        music_choices.append((sayonara_name, FP_SAYO_NARA))

        # grab custom music
        __scanCustomBGM(music_choices)

        # separte the music choices into pages
        music_pages = __paginate(music_choices)


    def setUserVolume(value, channel):
        """
        Sets user volume to the given value.
        NOTE: this does a preference edit, so there's no delay options.
        NOTE: this changes mixer volume, so it may affect other channels.

        IN:
            value - value to set volume to. Should be between 0.0 and 1.0.
            channel - channel to set.
        """
        chan = renpy.audio.audio.get_channel(channel)
        if chan.mixer in renpy.game.preferences.volumes:
            renpy.game.preferences.volumes[chan.mixer] = _sanitizeVolume(value)


    def _sanitizeVolume(value):
        """
        Santizes the given value as if it were a volume.
        NOTE: does not check if its a number.

        IN:
            value - value to sanitize

        RETURNS: valid volume value
        """
        if value < 0.0:
            return 0.0
        elif value > 1.0:
            return 1.0
        return value


    def __paginate(music_list):
        """
        Paginates the music list and returns a dict of the pages.

        IN:
            music_list - list of music choice tuples (see initMusicChoices)

        RETURNS:
            dict of music choices, paginated nicely:
            [0]: first page of music
            [1]: next page of music
            ...
            [n]: last page of music
        """
        pages_dict = dict()
        page = 0
        leftovers = music_list
        while len(leftovers) > 0:
            music_page, leftovers = __genPage(leftovers)
            pages_dict[page] = music_page
            page += 1

        return pages_dict


    def __genPage(music_list):
        """
        Generates the a page of music choices

        IN:
            music_list - list of music choice tuples (see initMusicChoices)

        RETURNS:
            tuple of the following format:
                [0] - page of the music choices
                [1] - reamining items in the music_list
        """
        return (music_list[:PAGE_LIMIT], music_list[PAGE_LIMIT:])


    def __scanCustomBGM(music_list):
        """
        Scans the custom music directory for custom musics and adds them to
        the given music_list.

        IN/OUT:
            music_list - list of music tuples to append to
        """
        # TODO: make song names / other tags configurable

        # No custom directory? abort
        if not os.access(custom_music_dir, os.F_OK):
            return

        # get the oggs
        found_files = os.listdir(custom_music_dir)
        found_oggs = [
            ogg_file
            for ogg_file in found_files # these are not all just oggs.
            if (
                isValidExt(ogg_file)
                and os.access(custom_music_dir + ogg_file, os.R_OK)
            )
        ]

        if len(found_oggs) == 0:
            # no custom songs found, please move on
            return

        # otherwise, we got some songs to add
        for ogg_file in found_oggs:
            # time to tag
            filepath = custom_music_dir + ogg_file

            _audio_file, _ext = _getAudioFile(filepath)

            if _audio_file is not None:
                # we only care if we even have an audio file
                disp_name = _getDispName(_audio_file, _ext, ogg_file)

                # loop prefix
                loop_prefix = _getLoopData(_audio_file, _ext)

                # add to the menu
                music_list.append((
                    cleanGUIText(disp_name),
                    loop_prefix + custom_music_reldir + ogg_file
                ))

                # we added something!
                store.persistent._mas_pm_added_custom_bgm = True


    def _getAudioFile(filepath):
        """
        Atteempts to retrive the correct audio object based on file extension

        IN:
            filepath - full filepath to the audio file we want

        RETURNS:
            tuple of the following format:
            [0]: audio object we want (May be None if this failed to load)
            [1]: extension of this audio object
        """
        if filepath.endswith(EXT_MP3):
            return (_getMP3(filepath), EXT_MP3)

        elif filepath.endswith(EXT_OGG):
            return (_getOgg(filepath), EXT_OGG)

        elif filepath.endswith(EXT_OPUS):
            return (_getOpus(filepath), EXT_OPUS)

        # otherwise, failure
        return (None, None)


    def _getDispName(_audio_file, _ext, _filename):
        """
        Attempts to retreive the display name for an audio file
        If that fails, then it will use the _filename as song name, minus
        extension.

        IN:
            _audio_file - audio object
            _ext - extension of the audio file
            _filename - filename of the audio file

        RETURNS:
            The name of this Song (probably)
        """
        disp_name = None

        if _audio_file.tags is not None:
            if _ext == EXT_MP3:
                disp_name = _getMP3Name(_audio_file)

            elif _ext == EXT_OGG:
                disp_name = _getOggName(_audio_file)

            elif _ext == EXT_OPUS:
                disp_name = _getOggName(_audio_file)

        if not disp_name:
            # let's just use filename minus extension at this point
            return _filename[:-(len(_ext))]

        return disp_name


    def _getLoopData(_audio_file, _ext):
        """
        Attempts to retrieve loop data from the given audio file and
        generates the appropraite string to put in front of the file name

        IN:
            _audio_file - audio object
            _ext - extension of hte audio file

        RETURNS:
            loop string, or and empty string if no loop string available
        """
        if _audio_file.tags is None:
            return ""

        if _ext == EXT_MP3:
            # NOTE: we do not support mp3 looping atm
            return ""

        if _ext == EXT_OGG:
            return _getOggLoop(_audio_file, _ext)

        elif _ext == EXT_OPUS:
            return _getOggLoop(_audio_file, _ext)

        return ""


    def _getMP3(filepath):
        """
        Attempts to retrieve the MP3 object from the given audio file

        IN:
            filepath - full filepath to the mp3 file want tags from

        RETURNS:
            mutagen.mp3.EasyMP3 object, or None if we coudlnt do it
        """
        try:
            return muta3.EasyMP3(filepath)
        except:
            return None


    def _getMP3Name(_audio_file):
        """
        Attempts to retrieve song name from mp3 id3 tag

        IN:
            _audio_file - audio object

        RETURNS:
            The display name for this song, or None if not possible
        """
        # NOTE: because we are using EasyID3, we can do the same thing Ogg
        #   does
        return _getOggName(_audio_file)


    def _getOgg(filepath):
        """
        Attempts to retreive the Ogg object from the given audio file

        IN:
            filepath - full filepath to the ogg file

        RETURNS:
            mutagen.ogg.OggVorbis or None if we coudlnt get the info
        """
        try:
            return mutaogg.OggVorbis(filepath)
        except:
            return None


    def _getOggName(_audio_file):
        """
        Attempts to retreive song name from Ogg tag

        IN:
            _audio_file - audio object

        RETURNS:
            The display name for this song, or None if not possible
        """
        song_names = _audio_file.tags.get(MT_TITLE, [])
        song_artists = _audio_file.tags.get(MT_ARTIST, [])

        if not song_names:
            # we need the song name at the very least to do this
            return None

        # we will select the first item by default. No custommization here
        sel_name = song_names[0]

        # if we have an artist, we'll pair the two and ship it as display name
        if song_artists:
            sel_art = song_artists[0]
            return sel_art + "  -  " + sel_name

        # otherwise, just name is fine
        return sel_name


    def _getOggLoop(_audio_file, _ext):
        """
        Attempts to retreive loop data from Ogg tags

        IN:
            _audio_file - audio object
            _ext - extension of the audio file

        RETURNS:
            the loop string we should use, or "" if no loop
        """
        # first, try MAS tags
        loopstart = _audio_file.tags.get(MT_LSTART, [])
        loopend = _audio_file.tags.get(MT_LEND, [])

        if loopstart or loopend:
            return _getOggLoopMAS(loopstart, loopend, _audio_file)

        # if not found, double check that we are ogg before continuing
        if _ext != EXT_OGG:
            return ""

        # if ogg, we can try the RPGMaker sample tags
        loopstart = _audio_file.tags.get(MT_LSSTART, [])
        looplen = _audio_file.tags.get(MT_LSEND, [])

        if loopstart:
            return _getOggLoopRPG(loopstart, looplen, _audio_file)

        return ""


    def _getOggLoopMAS(loopstart, loopend, _audio_file):
        """
        Attempts to retrieve MAS-based loop data from Ogg tags

        IN:
            loopstart - list of loopstart tags
            loopend - list of loopend tags
            _audio_file - audio object

        RETURNS:
            the loop string we should use or "" if no loop
        """
        # now try to float these values
        try:
            if loopstart:
                loopstart = float(loopstart[0])

            else:
                loopstart = None

            if loopend:
                loopend = float(loopend[0])

            else:
                loopend = None

        except:
            # error in parsing loop tags? just assume invalid all the way
            return ""

        # otherwise, we now have floats
        # validate these values
        if loopstart is not None and loopstart < 0:
            loopstart = 0

        if loopend is not None and loopend > _audio_file.info.length:
            loopend = None

        # NOTE: we shoudl for sure have at least one of these tags by now
        # now we can build the tag
        _tag_elems = [RPY_START]

        if loopstart is not None:
            _tag_elems.append(RPY_FROM)
            _tag_elems.append(str(loopstart))

        if loopend is not None:
            _tag_elems.append(RPY_TO)
            _tag_elems.append(str(loopend))

        _tag_elems.append(RPY_END)

        return " ".join(_tag_elems)


    def _getOggLoopRPG(loopstart, looplen, _audio_file):
        """
        Attempts to retrieve RPGMaker-based loop data form Ogg tags

        NOTE: unlike the MAS tags, loopstart is REQUIRED

        IN:
            loopstart - list of loopstart tags
            looplen - list of loop length tags
            _audio_file - audio object

        RETURNS:
            the loop string we should use or "" if no loop
        """
        # int these values
        try:
            loopstart = int(loopstart[0])

            if looplen:
                looplen = int(looplen[0])

            else:
                looplen = None

        except:
            # error in parsing tags.
            return ""

        # now we have ints
        # convert these into seconds
        _sample_rate = float(_audio_file.info.sample_rate)
        loopstart = loopstart / _sample_rate

        if looplen is not None:
            looplen = looplen / _sample_rate

        # validations
        if loopstart < 0:
            loopstart = 0

        loopend = None
        if looplen is not None:

            # calculate endpoint
            loopend = loopstart + looplen

            if loopend > _audio_file.info.length:
                loopend = None

        # now we can bulid the tag
        _tag_elems = [
            RPY_START,
            RPY_FROM,
            str(loopstart)
        ]

        if loopend is not None:
            _tag_elems.append(RPY_TO)
            _tag_elems.append(str(loopend))

        _tag_elems.append(RPY_END)

        return " ".join(_tag_elems)


    def _getOpus(filepath):
        """
        Attempts to retrieve the Opus object from the given audio file

        IN:
            filepath - full filepath to the opus file

        RETURNS:
            mutagen.ogg.OggOpus or None if we couldnt get the info
        """
        try:
            return mutaopus.OggOpus(filepath)
        except:
            return None


    def isValidExt(filename):
        """
        Checks if the given filename has an appropriate extension

        IN:
            filename - filename to check

        RETURNS:
            True if valid extension, false otherwise
        """
        for ext in VALID_EXT:
            if filename.endswith(ext):
                return True

        return False


    def cleanGUIText(unclean):
        """
        Cleans the given text so its applicable for gui usage

        IN:
            unclean - unclean text

        RETURNS:
            cleaned text
        """
        # bad text to be removed:
        bad_text = ("{", "}", "[", "]")

        # NOTE: for bad text, we just replace with empty
        cleaned_text = unclean
        for bt_el in bad_text:
            cleaned_text = cleaned_text.replace(bt_el, "")

        return cleaned_text


    def isInMusicList(filepath):
        """
        Checks if the a song with the given filepath is in the music choices
        list

        IN:
            filepath - filepath of song to check

        RETURNS:
            True if filepath is in the music_choices list, False otherwise
        """
        for name,fpath in music_choices:
            if filepath == fpath:
                return True

        return False


    # defaults
#    FIRST_PAGE_LIMIT = 10
    PAGE_LIMIT = 10
    current_track = "bgm/m1.ogg"
    selected_track = current_track
    menu_open = False

    # enables / disables the music menu
    # NOTE: not really used
    enabled = True

    vol_bump = 0.1 # how much to increase volume by

    # contains the song list
    music_choices = list()
    music_pages = dict() # song pages dict

    # custom music directory
    custom_music_dir = "custom_bgm"
    custom_music_reldir = "../" + custom_music_dir + "/"

    # valid extensions for music
    # NOTE: Renpy also supports WAV, but only uncompressed PCM, so lets not
    #   assume that the user knows how to change song formats.
    EXT_OPUS = ".opus"
    EXT_OGG = ".ogg"
    EXT_MP3 = ".mp3"
    VALID_EXT = [
        EXT_OPUS,
        EXT_OGG,
        EXT_MP3
    ]

    # metadata tags
    MT_TITLE = "title"
    MT_ARTIST = "artist"

    # NOTE: we default looping, so think of this as loop start and loop end
    # seconds to start playback
    MT_LSTART = "masloopstart"

    # seconds to end playback
    MT_LEND = "masloopend"

    # for RPGMaker support
    # samples to start playback
    MT_LSSTART = "loopstart"

    # length of loop
    MT_LSEND = "looplength"

    # renpy audio tags
    RPY_START = "<"
    RPY_FROM = "loop"
    RPY_TO = "to"
    RPY_END = ">"


# some post screen init is setting volume to current settings
init 10 python in songs:

    # for muting
    music_volume = getVolume("music")

# non store post inint stuff
init 10 python:

    # setupthe custom music directory
    store.songs.custom_music_dir = (
        config.basedir + "/" + store.songs.custom_music_dir + "/"
    ).replace("\\", "/")

    if (
            persistent.playername.lower() == "sayori"
            and not persistent._mas_sensitive_mode
        ):
        # sayori specific

        # init choices
        store.songs.initMusicChoices(True)

        # setup start songs
        store.songs.current_track = store.songs.FP_SAYO_NARA
        store.songs.selected_track = store.songs.FP_SAYO_NARA
        persistent.current_track = store.songs.FP_SAYO_NARA

    else:
        # non sayori stuff

        # init choices
        store.songs.initMusicChoices(False)

        # double check track existence
        if not store.songs.isInMusicList(persistent.current_track):
            # non existence song becomes No Music
            persistent.current_track = None

        # setup start songs
        store.songs.current_track = persistent.current_track
        store.songs.selected_track = store.songs.current_track

init -999 python:
    import re
    import pygame

    class MASMusicPlayer(object):
        """
        """
        MUSIC_CHANNEL = "music"
        MUSIC_TAGS_PATTERN = re.compile(r"^(?:<(?P<tags>.+?)>)?(?P<track>.+)")

        def __init__(self, loop=True, fadeout=0.0, fadein=0.0, tight=None):
            """
            Constructor

            IN:
                fadeout - default fadeout
                fadein - default fadein
                loop - whether or not we loop by default
                tight - whether or not we span fideouts into the next song
            """
            self.loop = loop
            self.fadeout = fadeout
            self.fadein = fadein
            self.tight = tight

            # self._playing = False
            self.enabled = True
            self._queued_track_id = None
            self.current_queue = list()
            self.playlists = dict()
            self.current_playlist = None

            renpy.music.set_queue_empty_callback(self._progress_queue, channel=MASMusicPlayer.MUSIC_CHANNEL)

        def is_enableed(self):
            return self.enabled

        def enable(self):
            self.enabled = True

        def disable(self):
            self.enabled = False
            self.stop()

        # def is_playing(self):
        #     """
        #     Checks if this player is currently playing something

        #     OUT:
        #         boolean
        #     """
        #     return self._playing and renpy.music.is_playing(MASMusicPlayer.MUSIC_CHANNEL)

        def add_playlist(self, id, *songs):
            """
            Defines a playlist
            NOTE: this will rewrite the playlist if it already exists
            NOTE: this allows to define empty playlists

            IN:
                id - id for the playlist
                songs - songs for the playlist
            """
            self.playlists[id] = list(songs)

        def get_playlist(self, id):
            """
            Returns a playlist by its id

            IN:
                id - id of the playlist
            """
            return self.playlists.get(id)

        def remove_playlist(self, id):
            """
            Removes a playlist by its id
            NOTE: safe

            IN:
                id - id of the playlist
            """
            if id in self.playlists:
                self.playlists.pop(id)

        def __validate_curr_track_for_playlist(self, id):
            """
            Validates the current track with a playlist

            IN:
                id - id of the playlist
            """
            if self.current_playlist == id:
                curr_track = renpy.music.get_playing(channel=MASMusicPlayer.MUSIC_CHANNEL)
                if curr_track is not None:
                    try:
                        curr_track_id = pl.index(curr_track)

                    except ValueError:
                        pass

                    else:
                        pl.insert(pl.pop(curr_track_id), 0)
                        self._queued_track_id = 0

        def sort_playlist(self, id):
            """
            Sorts a playlist

            IN:
                id - id of the playlist
            """
            pl = self.get_playlist(id)
            if pl is not None:
                pl.sort()
                self.__validate_curr_track_for_playlist(id)

        def shuffle_playlist(self, id):
            """
            Shuffles a playlist

            IN:
                id - id of the playlist
            """
            pl = self.get_playlist(id)
            if pl is not None:
                random.shuffle(pl)
                self.__validate_curr_track_for_playlist(id)

        def play_playlist(self, id):
            """
            Starts a playlist

            IN:
                id - id of the playlist
            """
            pl = self.get_playlist(id)
            if pl is not None:
                self.current_playlist = id
                self.queue(pl)

        def stop(self, fadeout=None):
            """
            Stops the music

            IN:
                fadeout - fadeout
                    (Default: None)
            """
            if fadeout is None:
                fadeout = self.fadeout

            renpy.music.stop(channel=MASMusicPlayer.MUSIC_CHANNEL, fadeout=fadeout)

        @classmethod
        def __get_queued_tracks(cls):
            """
            """
            c = renpy.music.get_channel(name=cls.MUSIC_CHANNEL)
            if c is not None:
                return c.queue

            return []

        @classmethod
        def __get_queued_tracks_fn(cls):
            """
            """
            return [qe.filename for qe in cls.__get_queued_tracks()]

        def _progress_queue(self, force=False):
            """
            """
            if not self.enabled or MASMusicPlayer.__get_queued_tracks():
                return

            max_id = len(self.current_queue) - 1
            # We can get -1 only if we have no queued tracks
            if max_id < 0:
                return

            old_id = self._queued_track_id

            # If we haven't played anything yet, start from 0
            if self._queued_track_id is None:
                self._queued_track_id = 0

            # If we finished this queue, start from 0 again
            elif self._queued_track_id >= max_id:
                self._queued_track_id = 0

            # Otherwise increment
            else:
                self._queued_track_id += 1

            qe_obj = self.current_queue[self._queued_track_id]

            # if qe_obj.filename not in MASMusicPlayer.__get_queued_tracks_fn():
            if not qe_obj.loop:
                self.current_queue.pop(self._queued_track_id)

            renpy.music.queue(
                qe_obj.filename,
                channel=MASMusicPlayer.MUSIC_CHANNEL,
                loop=False,
                clear_queue=False,
                fadein=qe_obj.fadein,
                tight=qe_obj.tight
            )

            # else:
            #     self._queued_track_id = old_id

        def queue(self, songs, loop=None, clear_queue=True, fadeout=None, fadein=None, tight=None):
            """
            Queues a song

            IN:
                songs - songs to play. Can be a single string or a list of strings
                loop - whether or not we loop this song
                    (Default: None)
                clear_queue - whether or not we clear the queue
                fadeout - fadeout for this song
                    (Default: None)
                fadein - fadein for this song
                    (Default: None)
                tight - whether or not we span fideout into the next song
                    (Default: None)
            """
            if not isinstance(songs, (tuple, list)):
                songs = [songs]

            if not songs:
                return

            new_queue = list()
            if loop is None:
                loop = self.loop
            if fadeout is None:
                fadeout = self.fadeout
            if fadein is None:
                fadein = self.fadein
            if tight is None:
                tight = self.tight

            for song in songs:
                if renpy.loadable(song):
                    new_queue.append(
                        renpy.audio.audio.QueueEntry(
                            song,
                            loop=loop,
                            fadein=fadein,
                            tight=tight
                        )
                    )

            if not new_queue:
                return

            if clear_queue:
                self.stop(fadeout=fadeout)
                self.current_queue[:] = new_queue
                self._queued_track_id = None
                self._progress_queue()

            else:
                old_queue_fns = [qe.filename for qe in self.current_queue]
                self.current_queue += new_queue
                queue_entries = MASMusicPlayer.__get_queued_tracks()
                queue_entries[:] = filter(lambda qe: qe.filename not in old_queue_fns, queue_entries)

        def play(self, songs, loop=None, fadeout=None, fadein=None, tight=None):
            """
            Plays a song (basically an alias to queue)

            IN:
                songs - songs to play. Can be a single string or a list of strings
                loop - whether or not we loop this song
                    (Default: None)
                fadeout - fadeout for this song
                    (Default: None)
                fadein - fadein for this song
                    (Default: None)
                tight - whether or not we span fideout into the next song
                    (Default: None)
            """
            self.queue(songs, loop=loop, clear_queue=True, fadeout=fadeout, fadein=fadein, tight=tight)

        def is_paused(self):
            """
            """
            return renpy.music.get_pause(channel=MASMusicPlayer.MUSIC_CHANNEL)

        def pause(self):
            """
            """
            if not self.is_paused():
                renpy.music.set_pause(True, channel=MASMusicPlayer.MUSIC_CHANNEL)

        def unpause(self):
            """
            """
            if self.is_paused():
                renpy.music.set_pause(False, channel=MASMusicPlayer.MUSIC_CHANNEL)

        @classmethod
        def get_position(cls):
            """
            """
            pos = renpy.music.get_pos(channel=cls.MUSIC_CHANNEL)
            return pos or 0.0

        @classmethod
        def get_duration(cls):
            """
            """
            duration = renpy.music.get_duration(channel=cls.MUSIC_CHANNEL)
            return duration or 1.0

        @classmethod
        def set_position(cls, value):
            """
            """
            curr_track = renpy.music.get_playing(channel=cls.MUSIC_CHANNEL)
            if curr_track is None:
                return

            new_tags = ""
            from_value = str(min(max(0.0, value), cls.get_duration()))
            to_value = None
            loop_value = None

            new_tags += "from " + from_value

            match = re.match(cls.MUSIC_TAGS_PATTERN, curr_track)
            # Technically we should always match
            if match is not None:
                tags = match.group("tags")
                track = match.group("track")

                if tags is not None:
                    tag_list = tags.split()
                    # We always expect a pair of a tag and its value
                    while len(tag_list) >= 2:
                        value = tag_list.pop()
                        tag = tag_list.pop()

                        if tag == "to":
                            to_value = value
                        elif tag == "loop":
                            loop_value = value

                    if to_value is not None:
                        if new_tags:
                            new_tags += " "
                        new_tags += "to " + to_value
                    if loop_value is not None:
                        if new_tags:
                            new_tags += " "
                        new_tags += "loop " + loop_value

                # Only add these if we have any tags
                if new_tags:
                    new_tags = "<" + new_tags + ">"

                # This should never be None, but just in case
                if track is not None:
                    new_track = new_tags + track
                    # TODO: might need to restore the queue here
                    renpy.music.play(
                        new_track,
                        channel=cls.MUSIC_CHANNEL,
                        loop=False,
                        fadeout=0.0,
                        fadein=0.0,
                        tight=False
                    )

    class MASBarAdjustment(renpy.display.behavior.Adjustment):
        """
        Represent a value that can be adjusted. This overrides a method of the original class.
        (see renpy.display.behavior.Adjustment)
        """
        def change(self, value, run_callback=True):
            """
            Basically a value setter for this adjustment

            IN:
                value - value for this adjustment
                run_callback - whether or not we run the callback (if we have one)
                    (Default: True)

            CHANGES: adds the run_callback param. This allows us to control when we run the callback
                (e.g. when the value changed by user or internally)
            """
            if value < 0:
                value = 0
            if value > self._range:
                value = self._range

            if value != self._value:
                self._value = value
                for d in renpy.display.behavior.adj_registered.setdefault(self, [ ]):
                    renpy.display.render.redraw(d, 0)
                if run_callback and self.changed:
                    # NOTE: we expect the bar to convert this into int
                    return self.changed(value)

            return None

    class MASAudioPositionValue(store.AudioPositionValue):
        """
        A value that shows the playback position of the audio file playing
        in a channel.
        (see AudioPositionValue)
        """
        def __init__(self, channel="music", update_interval=0.1, **adjustment_params):
            """
            Constructor

            IN:
                channel - channel we keep track of
                update_interval - how often the value updates, in seconds
                adjustment_params - params to pass in the adjustment object

            CHANGES:
                defines its adjustment (using MASBarAdjustment) in __init__
            """
            self.channel = channel
            self.update_interval = update_interval

            pos, duration = self.get_pos_duration()
            if "value" not in adjustment_params:
                adjustment_params["value"] = pos
            if "range" not in adjustment_params:
                adjustment_params["range"] = duration
            if "step" not in adjustment_params:
                adjustment_params["step"] = 1
            self.adjustment = MASBarAdjustment(**adjustment_params)

        def get_adjustment(self):
            """
            Getter for the adjustment object

            CHANGES:
                instead of creating a new one, returns the one we defined earlier
            """
            return self.adjustment

        def periodic(self, st):
            """
            A callback that periodically runs

            IN:
                st - shown timebase for this object

            CHANGES:
                passes an additional param to the change method of the adjustment
            """
            pos, duration = self.get_pos_duration()

            self.adjustment.set_range(duration)
            self.adjustment.change(pos, run_callback=False)

            return self.update_interval

    class MASMusicBar(renpy.display.behavior.Bar):
        """
        A bar that represents the current position of a track and allows to change it.
        This overrides some of the methods.
        (see renpy.display.behavior.Bar)
        """
        def __init__(
            self,
            range=None,
            value=None,
            width=None,
            height=None,
            changed=None,
            adjustment=None,
            step=None,
            page=None,
            bar=None,
            style=None,
            vertical=False,
            replaces=None,
            hovered=None,
            unhovered=None,
            respected_events=(pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN),
            **properties
        ):
            """
            Constructor for this object.

            Parameters for this weren't documentated, but at least some of them self-explanatory.

            CHANGES:
                Adds the respected_events property, which defaults to a tuple of 2 event types: MOUSEMOTION and MOUSEBUTTONDOWN.
                If this bar is adjustable, then it respects only the event types in respected_events
            """
            self.value = None

            if adjustment is None:
                if isinstance(value, renpy.ui.BarValue):

                    if isinstance(replaces, renpy.display.behavior.Bar):
                        value.replaces(replaces.value)

                    self.value = value
                    adjustment = value.get_adjustment()
                    renpy.game.interface.timeout(0)

                    # TODO: clear this up when we get to r7
                    if store.mas_globals.is_r7:
                        tooltip = value.get_tooltip()
                        if tooltip is not None:
                            properties.setdefault("tooltip", tooltip)

                else:
                    adjustment = renpy.display.behavior.Adjustment(range, value, step=step, page=page, changed=changed)

            if style is None:
                if self.value is not None:
                    if vertical:
                        style = self.value.get_style()[1]
                    else:
                        style = self.value.get_style()[0]
                else:
                    if vertical:
                        style = "vbar"
                    else:
                        style = "bar"

            if width is not None:
                properties["xmaximum"] = width
            if height is not None:
                properties["ymaximum"] = height

            super(renpy.display.behavior.Bar, self).__init__(style=style, **properties)

            self.adjustment = adjustment
            self.focusable = True

            # These are set when we are first rendered.
            self.thumb_dim = 0
            self.height = 0
            self.width = 0
            self.hidden = False

            self.hovered = hovered
            self.unhovered = unhovered
            self.respected_events = respected_events

        def event(self, ev, x, y, st):
            """
            Event handler.

            CHANGES:
                converts bar value into int and restricts events to respected_events
            """
            if not self.focusable:
                return None

            if not self.is_focused():
                return None

            if self.hidden:
                return None

            range = self.adjustment.range
            old_value = self.adjustment.value
            value = old_value

            vertical = self.style.bar_vertical
            invert = self.style.bar_invert ^ vertical
            if invert:
                value = range - value

            grabbed = (renpy.display.focus.get_grab() is self)
            just_grabbed = False

            ignore_event = False

            if not grabbed and map_event(ev, "bar_activate"):
                # TODO: r7 clearup
                if store.mas_globals.is_r7:
                    renpy.display.tts.speak(renpy.minstore.__("activate"))
                else:
                    renpy.display.tts.speak("activate")
                renpy.display.focus.set_grab(self)
                self.set_style_prefix("selected_hover_", True)
                just_grabbed = True
                grabbed = True
                ignore_event = True

            if grabbed:

                if vertical:
                    increase = "bar_down"
                    decrease = "bar_up"
                else:
                    increase = "bar_right"
                    decrease = "bar_left"

                if map_event(ev, decrease):
                    # TODO: r7 clearup
                    if store.mas_globals.is_r7:
                        renpy.display.tts.speak(renpy.minstore.__("decrease"))
                    else:
                        renpy.display.tts.speak("decrease")
                    value -= self.adjustment.step
                    ignore_event = True

                if map_event(ev, increase):
                    # TODO: r7 clearup
                    if store.mas_globals.is_r7:
                        renpy.display.tts.speak(renpy.minstore.__("increase"))
                    else:
                        renpy.display.tts.speak("increase")
                    value += self.adjustment.step
                    ignore_event = True

                if ev.type in self.respected_events:

                    if vertical:

                        tgutter = self.style.fore_gutter
                        bgutter = self.style.aft_gutter
                        zone_height = self.height - tgutter - bgutter - self.thumb_dim
                        if zone_height:
                            value = (y - tgutter - self.thumb_dim / 2) * range / zone_height
                        else:
                            value = 0

                    else:
                        lgutter = self.style.fore_gutter
                        rgutter = self.style.aft_gutter
                        zone_width = self.width - lgutter - rgutter - self.thumb_dim
                        if zone_width:
                            value = (x - lgutter - self.thumb_dim / 2) * range / zone_width
                        else:
                            value = 0

                    ignore_event = True

                # if isinstance(range, int):
                #     value = int(value)
                value = int(value)

                if value < 0:
                    # TODO: r7 clearup
                    if store.mas_globals.is_r7:
                        renpy.display.tts.speak("")
                    value = 0

                if value > range:
                    # TODO: r7 clearup
                    if store.mas_globals.is_r7:
                        renpy.display.tts.speak("")
                    value = range

            if invert:
                value = range - value

            value = int(value)

            if grabbed and not just_grabbed and map_event(ev, "bar_deactivate"):
                # TODO: r7 clearup
                if store.mas_globals.is_r7:
                    renpy.display.tts.speak(renpy.minstore.__("deactivate"))
                else:
                    renpy.display.tts.speak("deactivate")
                self.set_style_prefix("hover_", True)
                renpy.display.focus.set_grab(None)
                # NOTE: We do NOT need any changes on release
                # if store.mas_globals.is_r7:
                #     # Invoke rounding adjustment on bar release
                #     value = self.adjustment.round_value(value, release=True)
                #     if value != old_value:
                #         rv = self.adjustment.change(value)
                #         if rv is not None:
                #             return rv

                #     raise renpy.display.core.IgnoreEvent()

                # else:
                ignore_event = True

            if value != old_value:
                if store.mas_globals.is_r7:
                    value = self.adjustment.round_value(value, release=False)
                rv = self.adjustment.change(value)
                if rv is not None:
                    return rv

            if ignore_event:
                raise renpy.display.core.IgnoreEvent()
            else:
                return None

# MUSIC MENU ##################################################################
# This is the music selection menu
###############################################################################

# here we are copying game_menu's layout

#style music_menu_outer_frame is empty
#style music_menu_navigation_frame is empty
#style music_menu_content_frame is empty
#style music_menu_viewport is gui_viewport
#style music_menu_side is gui_side
#style music_menu_scrollbar is gui_vscrollbar

#style music_menu_label is gui_label
#style music_menu_label_text is gui_label_text

#style music_menu_return_button is navigation_button
style music_menu_navigation_frame is game_menu_navigation_frame
style music_menu_navigation_frame_dark is game_menu_navigation_frame
style music_menu_content_frame is game_menu_content_frame
style music_menu_content_frame_dark is game_menu_content_frame
style music_menu_viewport is game_menu_viewport
style music_menu_side is game_menu_side
style music_menu_label is game_menu_label
style music_menu_label_dark is game_menu_label_dark
style music_menu_label_text is game_menu_label_text
style music_menu_label_text_dark is game_menu_label_text_dark

style music_menu_return_button is return_button

style music_menu_return_button_dark is return_button

style music_menu_return_button_text is navigation_button_text

style music_menu_return_button_text_dark is navigation_button_text_dark

style music_menu_prev_button is return_button

style music_menu_prev_button_dark is return_button

style music_menu_prev_button_text is navigation_button_text

style music_menu_prev_button_text_dark is navigation_button_text_dark

style music_menu_outer_frame is game_menu_outer_frame:
    background "mod_assets/music_menu.png"

style music_menu_outer_frame_dark is game_menu_outer_frame_dark:
    background "mod_assets/music_menu_d.png"

style music_menu_button is navigation_button

style music_menu_button_text is navigation_button_text:
    properties gui.button_text_properties("navigation_button")
    font store.mas_ui.music_menu_font
    color "#fff"
    outlines [(4, "#b59", 0, 0), (2, "#b59", 2, 2)]
    hover_outlines [(4, "#fac", 0, 0), (2, "#fac", 2, 2)]
    insensitive_outlines [(4, "#fce", 0, 0), (2, "#fce", 2, 2)]

style music_menu_button_text_dark is navigation_button_text:
    properties gui.button_text_properties("navigation_button")
    font store.mas_ui.music_menu_font
    color "#FFD9E8"
    outlines [(4, "#DE367E", 0, 0), (2, "#DE367E", 2, 2)]
    hover_outlines [(4, "#FF80B7", 0, 0), (2, "#FF80B7", 2, 2)]
    insensitive_outlines [(4, "#FFB2D4", 0, 0), (2, "#FFB2D4", 2, 2)]

style music_menu_music_bar:
    xysize (400, 25)
    thumb None
    left_bar Frame(renpy.config.gamedir.replace("\\", "/") + "/Submods/test music/" + "left_bar.png", 2, 2)
    right_bar Frame(renpy.config.gamedir.replace("\\", "/") + "/Submods/test music/" + "right_bar.png", 2, 2)
    right_gutter 1

define pr = "Submods/test music/procelio.mp3"
define rf = "Submods/test music/rift.mp3"
define sb = "Submods/test music/saber.mp3"
define mp = MASMusicPlayer()

# Music menu
#
# IN:
#   music_page - current page of music
#   page_num - current page number
#   more_pages - true if there are more pages left
#
screen music_menu(music_page, page_num=0, more_pages=False):
    modal True

    default tooltip = MASMouseFollowerTooltip(xmaximum=800, text_align=0.0)
    default apv = MASAudioPositionValue(changed=store.mp.set_position)

    # logic to ensure Return works
    if songs.current_track is None:
        $ return_value = songs.NO_SONG
    else:
        $ return_value = songs.current_track


    # allows the music menu to quit using hotkey
    key "noshift_M" action Return(return_value)
    key "noshift_m" action Return(return_value)

    zorder 200

    style_prefix "music_menu"

    frame:
        style "music_menu_outer_frame"


        label "Music Menu":
            align (0.0, 0.0)
            # pos (0, 0)
            xoffset 25
            yoffset -125

        # this part copied from navigation menu
        vbox:
            style_prefix "music_menu"

            # xpos gui.navigation_xpos
            # xalign 0.1
            # yalign 0.4
            align (0.0, 0.0)
            # xpos 0
            xoffset 10
            spacing gui.navigation_spacing

            # wonderful loop so we can dynamically add songs
            for name, song, tt in music_page:
                if tt:
                    textbutton _(name):
                        action Return(song)
                        hovered tooltip.Action(tt)

                else:
                    textbutton _(name):
                        action Return(song)

        vbox:
            yalign 1.0

            hbox:
                yoffset 10
                # dynamic prevous text, so we can keep button size alignments
                if page_num > 0:
                    textbutton _("<<<< Prev"):
                        style "music_menu_prev_button"
                        action Return(page_num - 1)

                else:
                    textbutton _(""):
                        style "music_menu_prev_button"
                        xsize 126
                        sensitive False

                if more_pages:
                    textbutton _("Next >>>>"):
                        style "music_menu_return_button"
                        action Return(page_num + 1)

            add MASMusicBar(value=apv, style="music_menu_music_bar"):
                xoffset 10
                yoffset -10
            # bar:
            #     xysize (400, 25)
            #     value store.apv
            #     # changed store.mp.set_position
            #     left_bar Frame(renpy.config.gamedir.replace("\\", "/") + "/Submods/test music/" + "left_bar.png", 2, 2)
            #     right_bar Frame(renpy.config.gamedir.replace("\\", "/") + "/Submods/test music/" + "right_bar.png", 2, 2)
            #     right_gutter 1

            textbutton _(songs.NO_SONG):
                style "music_menu_return_button"
                action Return(songs.NO_SONG)

            textbutton _("Return"):
                style "music_menu_return_button"
                action Return(return_value)

        add tooltip

    # timer 0.1:
    #     repeat True
    #     action Function(renpy.restart_interaction)

# sets locks and calls hte appropriate screen
label display_music_menu:
    # set var so we can block multiple music menus
    python:
        songs.menu_open = True
        song_selected = False
        curr_page = 0

    # loop until we've selected a song
    while not song_selected:

        # setup pages
        $ music_page = songs.music_pages.get(curr_page, None)

        if music_page is None:
            # this should never happen. Immediately quit with None
            return songs.NO_SONG

        # Repack here to add tooltips
        python:
            music_page = list(music_page)
            for id, data_tuple in enumerate(music_page):
                name, song = data_tuple
                if len(name) > 27:
                    tooltip = name
                    name = name[:25].strip() + "..."
                else:
                    tooltip = None

                data_tuple = (name, song, tooltip)
                music_page[id] = data_tuple

        # otherwise, continue formatting args
        $ next_page = (curr_page + 1) in songs.music_pages

        call screen music_menu(music_page, page_num=curr_page, more_pages=next_page)

        # obtain result
        $ curr_page = _return
        $ song_selected = _return not in songs.music_pages

    $ songs.menu_open = False
    return _return


init python:
    import store.songs as songs
    # important song-related things that need to be global


    def dec_musicvol():
        """
        Decreases the volume of the music channel by the value defined in songs.vol_bump

        ASSUMES:
            persistent.playername
        """
        # sayori cannot make the volume quieter
        if (
            persistent.playername.lower() != "sayori"
            or persistent._mas_sensitive_mode
        ):
            songs.adjustVolume(up=False)


    def inc_musicvol():
        """
        increases the volume of the music channel by the value defined in songs.vol_bump
        """
        songs.adjustVolume()


    def mute_music(mute_enabled=True):
        """
        Mutes and unmutes the music channel

        IN:
            mute_enabled - True means we are allowed to mute.
                False means we are not
        """
        curr_volume = songs.getUserVolume("music")
        # sayori cannot mute
        if (
                curr_volume > 0.0
                and (
                    persistent.playername.lower() != "sayori"
                    or persistent._mas_sensitive_mode
                )
                and mute_enabled
            ):
            songs.music_volume = curr_volume
            songs.setUserVolume(0.0, "music")
        else:
            songs.setUserVolume(songs.music_volume, "music")


    def play_song(song, fadein=0.0, loop=True, set_per=False, fadeout=0.0, if_changed=False):
        """
        literally just plays a song onto the music channel
        Also sets the currentt track

        IN:
            song - Song to play. If None, the channel is stopped
            fadein - Number of seconds to fade the song in
                (Default: 0.0)
            loop - True if we should loop the song if possible, False to not loop.
                (Default: True)
            set_per - True if we should set persistent track, False if not
                (Default: False)
            fadeout - Number of seconds to fade the song out
                (Default: 0.0)
            if_changed - Whether or not to only set the song if it's changing
                (Use to play the same song again without it being restarted)
                (Default: False)
        """
        if song is None:
            song = songs.FP_NO_SONG
            renpy.music.stop(channel="music", fadeout=fadeout)

        else:
            renpy.music.play(
                song,
                channel="music",
                loop=loop,
                synchro_start=True,
                fadein=fadein,
                fadeout=fadeout,
                if_changed=if_changed
            )

        songs.current_track = song
        songs.selected_track = song

        if set_per:
            persistent.current_track = song


    def mas_startup_song():
        """
        Starts playing either the persistent track

        Meant for usage in startup processes.
        """
        if persistent.current_track is not None:
            play_song(persistent.current_track, if_changed=True)


    def select_music():
        # check for open menu
        if songs.enabled and not songs.menu_open:

            # disable unwanted interactions
            mas_RaiseShield_mumu()

            # music menu label
            selected_track = renpy.call_in_new_context("display_music_menu")
            if selected_track == songs.NO_SONG:
                selected_track = songs.FP_NO_SONG

            # workaround to handle new context
            if selected_track != songs.current_track:
                play_song(selected_track, set_per=True)

            # unwanted interactions are no longer unwanted
            if store.mas_globals.dlg_workflow:
                # the dialogue workflow means we should only enable
                # music menu interactions
                mas_MUINDropShield()

            elif store.mas_globals.in_idle_mode:
                # to idle
                mas_mumuToIdleShield()

            else:
                # otherwise we can enable interactions normally
                mas_DropShield_mumu()
