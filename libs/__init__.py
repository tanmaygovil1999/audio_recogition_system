import matplotlib
i = 0
while i < 10:
    i += 1
    try:
        matplotlib.use('TkAgg')
        break
    except:
        print(i)

def x():
  print('XXX')
