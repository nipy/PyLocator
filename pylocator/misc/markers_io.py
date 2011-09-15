
def load_markers(fh):
    if type(fh)==str:
        fh = open(fh,"r")
    rv = []
    for line in fh.readlines():
        rv.append([])
        parts = line[:-1].split(",")
        rv[-1].append(parts[0])
        for i in range(1,len(parts)):
            rv[-1].append(float(parts[i]))
    return rv

if __name__=="__main__":
    fn = "/media/Extern/public/Experimente/AudioStroop/kombinierte_analyse/elec_pos/443.txt"
    print load_markers(fn)
    fh = open(fn,"r")
    print load_markers(fh)

