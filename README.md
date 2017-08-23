# PyBot

This is my first telegram bot written in Python

## Commands

```
/weather <City>     - Weather in a city for now, today and tommorow
/w <City>           - Short form of /w
/info               - Information about this bot  
/wset <City>        - Set default city for /weather
/ibash <Number>     - Random quote from ibash.org.ru
/loglist <Number>   - Random quote from loglist.net
/manage <SQL query> - Manage your database (Only for admins)
```

## Starting

```
git clone https://github.com/Cuttlerat/pybot.git
cd pybot
```

Add your telegram username, tokens, and database path into `./tokens.py` file
```
BOT_TOKEN = '<YOUR TOKEN>'
WEATHER_TOKEN = '<YOUR TOKEN>'
DATABASE = 'data/pybot.db'
ADMINS = [ 'YOUR TELEGRAM USERNAME WITHOUT @' ]
```

Then just launch the bot

```
./pybot.py
```

### Starting into a docker container

In order to build and create a docker container, `docker-compose` must be installed in your system

```
docker-compose up --build pybot 
```

You can get a weather token here: https://www.worldweatheronline.com/ <br>
Register your bot here: https://t.me/BotFather

## How to /manage database

If you want that your bot triggers on a some type of messages, there some options here.

### Google

If you want that your bot triggers on a messages like this
```
Cuttlerat: What is Jenkins?
Cuttlebot: https://www.google.ru/search?q=Jenkins
```

You will need to add a note in your database like this:

```
/manage INSERT INTO google(match) VALUES("what is")
```

All matches must be in a low case! It's important (I will do something with it later)

If you don't want any word to trigger this function

```
/manage INSERT INTO google_ignore(ignore) VALUES("Jenkins")
Cuttlerat: What is Jenkins?
*no answer*
```

### Simple trigger

If you want a simple trigger on a message responding with your specified string

```
/manage INSERT INTO answers(match,string) VALUES("hello!", "Hi!")
Cuttlerat: Hello!
Cutltebot: Hi!
```

### Ping

If you want to summon someone with just mentioning of his name or nickname

```
/manage INSERT INTO pingers(username,match) VALUES("Cuttlerat", "rat")
Cuttlerat: rat!
*nothing*
```

Why? Because we didn't set a ping phrase yet

```
/manage INSERT INTO ping_phrases(phrase) VALUES("ping")
Cuttlerat: ping rat
Cuttlebot: @Cuttlerat
```

There is a little trick to summon all persons from the pingers table

```
/manage INSERT INTO pingers(username,match) VALUES("hotkosc", "kosc")
/manage INSERT INTO pingers(username,match) VALUES("EVERYONE GET IN HERE", "all")
Cuttlerat: ping all
Cuttlebot: @Cuttlerat @hotkosc
```

But what if you want to call everyone except one guy?

You will need to add a ping exclude phrase

```
/manage INSERT INTO ping_exclude(match) VALUES("excpet")
Cuttlerat: ping all except kosc
Cuttlebot: @Cuttlerat
```

And is it! Enjoy your bot!
