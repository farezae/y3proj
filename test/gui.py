# import the library
from appJar import gui
from test.offline import playSounds 

# create a gui variable
app = gui("ecg melodies", "400x200")

# add & configure widgets
app.addButton(" play sounds ", playSounds)


 # start the GUI
app.go()