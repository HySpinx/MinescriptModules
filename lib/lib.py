import lib.minescript_plus as minescript_plus

def play_alert_sound():
    for i in range(6):
        minescript_plus.Util.play_sound(minescript_plus.Util.get_soundevents().BELL_BLOCK, minescript_plus.Util.get_soundsource().VOICE)