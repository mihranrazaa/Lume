---

title: "Lume"

author: "mihranrazaa"

description: "An Open Source alternative of Kindle "

created at: "2025-07-13"

---





----



**12 JULY**

- SO the plan is to build a alternative of kindle why? because from what i have seen on youtube, kindle can ban your account and your purchased books will be gone, sometimes when the deal between kindle and author of some book gets expired the books automatically vanishes from your account which is crazy, someone is paying full price but still he is not owning that piece, like it is not even a clooud service where subscription model is understandable.
- So yeah i thought to build a complete open source E book Reader "Lume" and this will be my first prototype...

---

**13 JULY**

- I have figured out my design i will make it, so today i first started by researching what components i will be using as i learnind in AMA if you are building a project which you want someone else to recreate use modules which is a good excuse to my lack of skills, so i selected Rpi zero 2w as my main MCU because it has wifi, blutooth and good support, i have a basic idea of what kind of software i want to build, so it is perfect for that, next i'm using 7.5inch e ink display with driver, vertically not horizontally which is giving more of real book page kind of vibe, then for inputs i first thought of five tactile push buttons for navigating and selecting but then i added a joystick and 4 tackile push buttons which will drastically improve user navigation as i'm building it for myself i think this will be a good choice so yeah also i will be using a battery hat for my pi zero 2w for poratbility ofc.....

- Alright so completed the schematics, i will be using 8pin cable to connect the driver to the main board, also i'm using 5D joystick because normal joystick module required ADC driver and i didn;t wanted to include it, and they both were same priced so i chose this, my idea of the CAD design is i can grab one side of the case with ease like it will be lifted from back and i will add pcb there, so yeah that works, now on to building pcb

- PCB DONEEE!!! so it is like a vertical strip, routing is good i have given adequate spacing for them so it should be fine, i enjoyed building this pcb lol, I've been working this whole day on this lol, i thought of this project yesterday and i now i have created it's PCB, Building is FUN. After coming back home i might start CAD let's see my plan is finishing this till 15th July....

- And yeah here are all the images: 

**Total 8Hrs+**

---

**14-15 JULY (CAD!!!!)**

- I forgot to write the Journal on 14th, i spent almost all day working on cad and didn't had energy to write journal lol, so this is the complete process of how i created my case.. I already had a basic idea in my mind, i didn't wanted to build a tab like reader so i searched some available reader and i found a very good concept basically there will be sleek display part and a elevated hardware part which will also work as grip to hold the reader, so i first start by taking mesurements of the display it is 7.5 inch display, so i already thought that i will rotat the display because it will look more like big book then that's why i created the pcb vertically rather then horizontal, so yeah,. That sums up the rough idea other things just came while doing it...

- I start by importing the pcb first to makesure the case fits in, i prefer to build over the components it give me confidence that the dimensions are coorect if i use a correct cad file lol, anyways then i created the rough sketch i first created them in one sketch but then i had to divide the base in 2-3 different parts as i'm noob and i was getting confused so it made easier to work with so i created the base extrusion nad basic stuff, then i started aligning and fixing the pcb place, i had to keep in mind that there will be a cable and driver board which will be connected in the pcb but there will also be wire from the display so i kept some gap so that wires can pass through, then i created the elevated part to which i used shell option in onshape, Then i thought becuase i was addding a grip olfring type thing why not add extrude inside where fingers will be placed for better grip, and it will also improve the look and it did!, so i added a cylindrical area in the elevated shell, then i added holes for my screwless design, i learned some more about snap fit designs and it is better to make the pins a bit bigger and add chaffer for enough friction, so i added 4mm and 3mm holes in the frame, Oh yeah i forgot to add that i added support for PCB and for pi zero 2 w and battery, then i started making it look good fixing small stuff checking dimensions, i added chaffer, fillet, also added more inside extrusion lines this time near the cylindrical holding area, then i added some writing in the case because why not.. Then i added 2 openings in the case, one for sd card and one for power, as i don't think it is needed any ports except power as there is only time that you have to add sd in pi zero and done filed will be uploaded via wifi or bluetooth, still because this is version 1 i did it anyways, with that my verision on ebase was ready and i moved to top...

- I started by taking dimensions of the main out frame i got confused a bit becuase of chaffer and fillet i was getting wrong dimensions i forgot about them then after realizing i fixed and it got write then added screen dimension and added input holes sketch oh yeah i forgot add thaat above anyways i put them in the correct place extruded the frame by 4-5mm then added chaffer and fillet, now when in assembly they are actually looking good, then i satrted taking dimesions of the holes and recreated that sketch in the the plate, added pin added chaffer, and pins were done, next i remved lume from back of base an added in the bottom of plate, after this the basic version was ready then i again touched up some parts and version 1 was ready.... checked if the pins are correctly ocnnecting or not and everything was fine, which leads us to right now i'm experimenting with colors i''m thinking of dark colour, and after this i have to start developing the code,i have to finish a alpha working code to ship it with the project i can work and improve the os with time...

- SO yeah that was the whole process of me building the case for Lume V1, ofc timelines are a bit different like not everything happend text by text i took breaks did other stuff returned worked on this and all, now i have to work on the code for this project, i have to shift the deadline to one more day, my previous goal was to ship the project on 15th july like a hackathon but it is isn't possible building the whole code in one day is not much possible for me i hope for the best....

- Here are all the images of building the CASE::

- **Total 15Hrs+**

---

