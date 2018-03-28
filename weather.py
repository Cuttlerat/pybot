def get_emoji(weather_status):
    emojis = {
        'Clouds': u'\U00002601',
        'Clear': u'\U00002600',
        'Rain': u'\U0001F327',
        'Extreme': u'\U0001F32A',
        'Snow': u'\U0001F328',
        'Thunderstorm': u'\U000026C8',
        'Mist': u'\U0001F32B',
        'Haze': u'\U0001F324',
        'notsure': u'\U0001F648'
    }

    return ("".join([emojis[i] for i in emojis if weather_status == i]))