import aiml
import telepot
import time

def handle(msg):
    chat_id = msg['chat']['id']
    command = msg['text']
    username = msg['from']['first_name']
    print 'Got command: %s' % command
    tbot.sendMessage(chat_id,bot.respond(command))

bot = aiml.Kernel()
bot.bootstrap(learnFiles = "std-startup.xml", commands = "LOAD AIML B")


    
tbot = telepot.Bot('221746913:AAGDtUMCEW0eLNJqjHC8YhEthz_PCCrfTnk')
tbot.message_loop(handle)
print 'I am listening ...'
while 1:
    time.sleep(10)