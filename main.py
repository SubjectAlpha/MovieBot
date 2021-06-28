import discord, os, random, validators, json, io, requests
from discord.ext.commands import Bot
from json import JSONEncoder
from types import SimpleNamespace
from bs4 import BeautifulSoup

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

def get_movie_queue(server_id):
  movie_queue = ""
  with io.open(f"{server_id}_queue.json", "r+", encoding="utf8") as queue:
      movie_queue = json.load(queue, object_hook=lambda d: SimpleNamespace(**d))
  return movie_queue

def getMovieDetails(url):
  data = {}
  r = requests.get(url=url)
  # Create a BeautifulSoup object
  soup = BeautifulSoup(r.text, 'html.parser')

  #page title
  title = soup.find('title')
  data["title"] = title.string

  # rating
  ratingValue = soup.find("span", {"itemprop" : "ratingValue"})
  data["ratingValue"] = ratingValue.string

  # no of rating given
  ratingCount = soup.find("span", {"itemprop" : "ratingCount"})
  data["ratingCount"] = ratingCount.string

  # name
  titleName = soup.find("div",{'class':'titleBar'}).find("h1")
  data["name"] = titleName.contents[0].replace(u'\xa0', u'')

  return data

@bot.command("add", help = "Usage: $add IMDB link")
async def add_to_list(context):
  create_if_not_exists_queue_file(context.guild.id)

  link = context.message.content.split(" ")[1]

  if validators.url(link):
    try:
      movie_queue = get_movie_queue(context.guild.id)

      with io.open(f"{context.guild.id}_queue.json", "w+", encoding="utf8") as queue:
        queue_item = QueueItem(context.author.id, link)
        movie_queue.movies.append(queue_item)
        json.dump(movie_queue, queue, cls=QueueEncoder)
      await context.reply(link + " added to queue")
    except FileNotFoundError:
      print("File not found!")
  else:
    context.reply("You must submit an IMDB link")

@bot.command("list")
async def get_movie_list_message(context):
  current_queue = get_movie_queue(context.guild.id)
  queue_msg = ""
  pos = 1
  for m in current_queue.movies:
    details = getMovieDetails(m.url)
    
    queue_msg += f"{details['title']} Rating: {details['ratingValue']} Position: {str(pos)}\n"
    pos += 1
  await context.reply("Current Queue:\n" + queue_msg)

@bot.command(name="pick")
async def pick_movie(context):
  current_queue = get_movie_queue(context.guild.id)
  pick = random.randint(0, len(current_queue.movies)-1)

  details = getMovieDetails(current_queue.movies[pick].url)

  await context.reply(f"You should watch: {details['title']} Rating: {details['ratingValue']}")

@bot.command(name="remove", help="Insert the position number to remove a movie from the queue")
async def remove_movie(context):
  movie_position = int(context.message.content.split(" ")[1])
  current_queue = get_movie_queue(context.guild.id)
  current_movie = current_queue.movies[movie_position - 1]
  current_queue.movies.pop(movie_position - 1)
  with io.open(f"{context.guild.id}_queue.json", "w+", encoding="utf8") as queue:
    json.dump(current_queue, queue, cls=QueueEncoder)
  await context.reply(f"Removed {current_movie.url}")

@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user}')
  
bot.run(os.environ['BOT_TOKEN'])
