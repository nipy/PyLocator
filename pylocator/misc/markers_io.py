def load_markers(fh):
    if type(fh)==str:
        fh = open(fh,"r")
    rv = []
    for line in fh.readlines():
        data_and_comment = line.split("#")
        if len(data_and_comment) == 1:
            data_part = data_and_comment[0][:-1] #strip newline at end
        else:
            data_part = data_and_comment[0] # ignore comment
        if len(data_part.strip()) == 0:
            continue
        new_item = []
        parts = data_part.split(",")
        new_item.append(parts[0])
        for i in range(1,len(parts)):
            new_item.append(float(parts[i]))
        rv.append(new_item)
    return rv

def load_markers_to_dict(fh):
    if type(fh)==str:
        fh = open(fh,"r")
    marker_list = []
    for line in fh.readlines():
        marker_list.append([])
        parts = line[:-1].split(",")
        marker_list[-1].append(parts[0])
        for i in range(1,len(parts)):
            marker_list[-1].append(float(parts[i]))
    return dict([(marker[0],marker[1:]) for marker in marker_list])

if __name__=="__main__":
    fn = "/media/Extern/public/Experimente/AudioStroop/kombinierte_analyse/elec_pos/443.txt"
    print load_markers(fn)
    fh = open(fn,"r")
    print load_markers(fh)

