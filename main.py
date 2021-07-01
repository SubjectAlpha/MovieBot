import os, random, validators, json, io, re
from discord.ext.commands import Bot
from json import JSONEncoder
from types import SimpleNamespace
from imdb import IMDb

#invite link https://discord.com/oauth2/authorize?client_id=858789129848225792&permissions=27712&scope=bot

class MovieQueue:
  def __init__(self, server_id):
    self.server_id = server_id
    self.movies = []

class QueueItem:
  def __init__(self, uid, link):
    self.uid = uid
    self.url = link

class QueueEncoder(JSONEncoder):
  def default(self, o):
    return o.__dict__

bot = Bot(command_prefix='$')

#Check to see if save file exists for the server, if it doesn't it creates one.
def create_if_not_exists_queue_file(server_id):
  path = f"{server_id}_queue.json"
  if os.path.isfile(path) and os.access(path, os.R_OK):
    # checks if file exists
    print ("File exists and is readable")
  else:
    print ("Either file is missing or is not readable, creating file...")
    with io.open(os.path.join(path), 'w') as queue:
      new_queue = MovieQueue(server_id)
      json.dump(new_queue, queue, cls=QueueEncoder)

#Return a list movie queue objects based on the server its called in
def get_movie_queue(server_id):
  movie_queue = ""
  with io.open(f"{server_id}_queue.json", "r+", encoding="utf8") as queue:
    movie_queue = json.load(queue, object_hook=lambda d: SimpleNamespace(**d))
  return movie_queue

def get_movie_details(url):
  data = {}
  ia = IMDb()

  if validators.url(url):
    url = url.split("/")
    temp = re.compile("([a-zA-Z]+)([0-9]+)")
    res = temp.match(url[4]).groups()
    mv = ia.get_movie(res[1])
    return mv

  return data

#Add a movie based on IMDb link
@bot.command("add", help = "Usage: $add IMDB link")
async def add_to_list(context):
  create_if_not_exists_queue_file(context.guild.id)

  link = context.message.content.split(" ")[1]

  if validators.url(link):
    imdb_check = re.compile("^https?:\/\/+([^:/]+\.)?imdb\.com\/title\/([-a-zA-Z0-9_\\+~#?&//=]*)")
    if imdb_check.match(link):
      try:
        movie_queue = get_movie_queue(context.guild.id)
        with io.open(f"{context.guild.id}_queue.json", "w+", encoding="utf8") as queue:
          queue_item = QueueItem(context.author.id, link)
          movie_queue.movies.append(queue_item)
          json.dump(movie_queue, queue, cls=QueueEncoder)
        await context.message.add_reaction("\N{THUMBS UP SIGN}")
      except FileNotFoundError:
        await context.reply("An unrecoverable error occurred")
    else:
      await context.reply("You must submit an IMDb link")
  else:
    await context.reply("You must submit an IMDb link")

#List all movies in current queue, and get info from IMDb about them.
@bot.command("list")
async def get_movie_list_message(context):
  current_queue = get_movie_queue(context.guild.id)
  queue_msg = ""
  pos = 1
  for m in current_queue.movies:
    details = get_movie_details(m.url)
    
    queue_msg += f"{details['title']} - {details['rating']}/10 - Position: {str(pos)}\n"
    pos += 1
  await context.reply("Current Queue:\n" + queue_msg)

#Psuedo randomly choose a movie from the saved list.
@bot.command(name="pick")
async def pick_movie(context):
  current_queue = get_movie_queue(context.guild.id)
  pick = random.randint(0, len(current_queue.movies)-1)

  details = get_movie_details(current_queue.movies[pick].url)

  await context.reply(f"You should watch: {details['title']} Rating: {details['rating']}")

#Remove a movie from the list based on its current queue position.
@bot.command(name="remove", help="Insert the position number to remove a movie from the queue")
async def remove_movie(context):
  movie_position = int(context.message.content.split(" ")[1])
  current_queue = get_movie_queue(context.guild.id)
  current_queue.movies.pop(movie_position - 1)
  with io.open(f"{context.guild.id}_queue.json", "w+", encoding="utf8") as queue:
    json.dump(current_queue, queue, cls=QueueEncoder)

  await context.message.add_reaction("\N{THUMBS UP SIGN}")

#Status message to know when the bot is ready.
@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user}')
  
bot.run(os.environ['BOT_TOKEN'])
