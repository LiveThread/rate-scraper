"""
Find the common subreddits shared by each month.
"""

january     = set(line.strip() for line in open('../data/january.txt'))
february    = set(line.strip() for line in open('../data/february.txt'))
march       = set(line.strip() for line in open('../data/march.txt'))
april       = set(line.strip() for line in open('../data/april.txt'))
may         = set(line.strip() for line in open('../data/may.txt'))
june        = set(line.strip() for line in open('../data/june.txt'))
july        = set(line.strip() for line in open('../data/july.txt'))
august      = set(line.strip() for line in open('../data/august.txt'))
september   = set(line.strip() for line in open('../data/september.txt'))
october     = set(line.strip() for line in open('../data/october.txt'))
november    = set(line.strip() for line in open('../data/november.txt'))
december    = set(line.strip() for line in open('../data/december.txt'))

intersection = january & february & march & april & may & june & july & august \
               & september & october & november & december

for s in intersection:
    print(s)
