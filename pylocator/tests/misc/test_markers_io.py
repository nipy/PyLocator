from cStringIO import StringIO
from pylocator.misc import markers_io

from nose.tools import assert_raises

valid_test_cases = {
"simple without labels" :
""",25.5092096987,-18.0000156769,37.0115808132,5.0,0.0,0.0,1.0
,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",

"simple with labels" : 
"""Fz,25.5092096987,-18.0000156769,37.0115808132,5.0,0.0,0.0,1.0
Cz,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
Pz,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",

"exponential notation in coordinate" : 
"""Fz,2.55E1,-18.0000156769,37.0115808132,5.0,0.0,0.0,1.0
Cz,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
Pz,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",

"exponential notation in radius" : 
"""Fz,25.5092096987,-18.0000156769,37.0115808132,5.0E-1,0.0,0.0,1.0
Cz,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
Pz,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",

"exponential notation in color" : 
"""Fz,25.5092096987,-18.0000156769,37.0115808132,5.0,0.0,0.0,2.0E-1
Cz,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
Pz,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",

"comment line in the beginning" : 
"""# This is a comment
Fz,25.5092096987,-18.0000156769,37.0115808132,5.0,0.0,0.0,1.0
Cz,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
Pz,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",

"comment for one coordinate" : 
"""Fz,25.5092096987,-18.0000156769,37.0115808132,5.0,0.0,0.0,1.0 # This is a comment
Cz,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
Pz,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",

"empty line" : 
"""Fz,25.5092096987,-18.0000156769,37.0115808132,5.0,0.0,0.0,1.0

Cz,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
Pz,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",
}

invalid_test_cases = {
"coordinate is no float" :
""",ERROR,-18.0000156769,37.0115808132,5.0,0.0,0.0,1.0
,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",

"not enough values" :
""",25.5092096987,-18.0000156769,37.0115808132,5.0,0.0,0.0
,46.686666807,-18.0000156769,-9.19378015049,5.0,0.0,0.0,1.0
,8.18219933732,-18.0000156769,11.5023711145,5.0,0.0,0.0,1.0""",
}

def test_reading_markers_from_filehandle():
    for k in valid_test_cases:
        yield read_markers_from_stringio, k, valid_test_cases[k]
        
def read_markers_from_stringio(key, file_content):
    sio = StringIO(file_content)
    markers = markers_io.load_markers(sio)
    assert len(markers)>0
    
def test_reading_invalid_markers_from_filehandle():
    for k in invalid_test_cases:
        yield invalid_data_raise_exception, k, invalid_test_cases[k]
        
def invalid_data_raise_exception(key, file_content):
    assert_raises(markers_io.FormatException, read_markers_from_stringio, key, file_content)
