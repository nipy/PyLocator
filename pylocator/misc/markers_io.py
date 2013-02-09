def load_markers(fh):
    """Reads all markers from a file to a list. Converts coordinates, radii and color 
    to float.
    
    :param fh: File handle open for reading or filename. If filename is given, 
    file will be opened in "r" mode.
    :type fh: file or string
    
    :returns: List of lists. Each marker is represented as a list with eight 
    values: label, x,y,z, radius, red, green, blue        
    """
    if type(fh)==str:
        fh = open(fh,"r")
    rv = []
    for idx, line in enumerate(fh.readlines()):
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
            try:
                new_item.append(float(parts[i]))
            except ValueError, ve:
                raise FormatException(ve)
        if not len(new_item)==8:
            raise FormatException("Not enough values in line %i" % idx)
        rv.append(new_item)
    return rv

def load_markers_to_dict(fh):
    """Reads all markers from a file to a dictionary. Converts coordinates, radii and color 
    to float. Using the same label for two or more times will hide some markers.
    
    :param fh: File handle open for reading or filename. If filename is given, 
    file will be opened in "r" mode.
    :type fh: file or string
    
    :returns: Dictionary of lists. Each marker is represented as a list with eight 
    values: label, x,y,z, radius, red, green, blue        
    """
    marker_list = load_markers(fh)
    return dict([(marker[0],marker[1:]) for marker in marker_list])

class FormatException(Exception):
    pass

if __name__=="__main__":
    fn = "/media/Extern/public/Experimente/AudioStroop/kombinierte_analyse/elec_pos/443.txt"
    print load_markers(fn)
    fh = open(fn,"r")
    print load_markers(fh)

