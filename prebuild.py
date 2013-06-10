import os

def run():
    libs = ['setuptools', 'bottle', 'dropbox', 'Cheetah']
    
    for i in libs:
        os.system('sudo easy_install %s' % i)

if __name__ == '__main__':
    run()
