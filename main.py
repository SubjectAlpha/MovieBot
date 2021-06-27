import discord, os, random

#invite link https://discord.com/oauth2/authorize?client_id=858789129848225792&permissions=27712&scope=bot

MOVIE_LIST_LINK = os.environ['MOVIE_LIST_LINK']

client = discord.Client()

async def get_movie_list_message():
  split_message = MOVIE_LIST_LINK.split("/")
  server_id = int(split_message[4])
  channel_id = int(split_message[5])
  msg_id = int(split_message[6])

  server = client.get_guild(server_id)
  channel = server.get_channel(channel_id)
  message = await channel.fetch_message(msg_id)

  return(message)

@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  if message.content.startswith('!movie'):
    msg = message.content.split(" ")
    if(msg[1] == "pick"):
      movie_list = await get_movie_list_message()
      movie_list = movie_list.content.split("\n")
      movie_list.pop(0)
      random_index = random.randint(0, len(movie_list)-1)
      await message.channel.send("New Pick: " + movie_list[random_index])
    elif(msg[1] == "request"):
      print("add movie to list here/add voting system?")

client.run(os.environ['BOT_TOKEN'])