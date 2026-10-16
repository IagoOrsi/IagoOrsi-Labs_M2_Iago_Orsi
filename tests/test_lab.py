import cv2, numpy as np, pytest
from pdi_lab.__main__ import segment, component_rows, analyze

def test_fixed_threshold_boundaries():
    image=np.array([[119,120,121]],dtype=np.uint8)
    mask=segment(image,"fixed",120)
    assert mask.tolist()==[[0,0,255]]

def test_diagonal_connectivity(tmp_path):
    mask=np.zeros((3,3),np.uint8); mask[0,0]=255; mask[1,1]=255
    assert len(component_rows(mask,4,0)[0])==2
    assert len(component_rows(mask,8,0)[0])==1

def test_opening_removes_isolated_noise():
    mask=np.zeros((15,15),np.uint8); mask[7,7]=255; mask[4:11,4:11]=255
    out=cv2.morphologyEx(mask,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
    assert out[7,7]==255
    assert out[0,0]==0

def test_empty_mask(tmp_path):
    mask=np.zeros((10,10),np.uint8)
    result=analyze(mask,str(tmp_path/"empty"),8,0,3,1)
    assert result["final"]["components_raw"]==0

def test_invalid_connectivity(tmp_path):
    with pytest.raises(ValueError):
        analyze(np.zeros((3,3),np.uint8),str(tmp_path/"x"),6,0,3,1)

def test_binary_validation(tmp_path):
    m=np.array([[0,128],[255,0]],np.uint8)
    with pytest.raises(ValueError):
        analyze(m,str(tmp_path/"x"),8,0,3,1)
