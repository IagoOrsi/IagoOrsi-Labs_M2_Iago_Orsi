import argparse, csv, json, sys
from pathlib import Path
import cv2
import numpy as np

def read_image(path, grayscale=False):
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Não foi possível ler a imagem: {path}")
    return image

def segment(image, method="fixed", threshold=120, invert=False, block_size=11, c=2,
            hsv_lower=None, hsv_upper=None):
    if method not in {"fixed","otsu","adaptive","hsv"}:
        raise ValueError(f"Método desconhecido: {method}")
    if method in {"fixed","otsu","adaptive"}:
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if method == "fixed":
            if not 0 <= threshold <= 255: raise ValueError("--threshold deve estar entre 0 e 255")
            flag = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
            _, mask = cv2.threshold(gray, threshold, 255, flag)
        elif method == "otsu":
            flag = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
            _, mask = cv2.threshold(gray, 0, 255, flag | cv2.THRESH_OTSU)
        else:
            if block_size < 3 or block_size % 2 == 0: raise ValueError("--block-size deve ser ímpar e >= 3")
            flag = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
            mask = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,flag,block_size,c)
    else:
        if image.ndim == 2: image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
        lo=np.array(hsv_lower if hsv_lower is not None else [0,0,0],dtype=np.uint8)
        hi=np.array(hsv_upper if hsv_upper is not None else [179,255,255],dtype=np.uint8)
        if np.any(lo>hi): raise ValueError("Cada limite HSV inferior deve ser <= ao superior")
        mask=cv2.inRange(hsv,lo,hi)
    return mask

def save_mask(mask, path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    values=set(np.unique(mask).tolist())
    if mask.ndim != 2 or not values.issubset({0,255}):
        raise ValueError("Máscara deve ter um canal e conter somente 0 e 255")
    if not cv2.imwrite(str(path),mask): raise ValueError(f"Falha ao salvar: {path}")
    ratio=float(np.count_nonzero(mask))/mask.size if mask.size else 0
    print(f"width={mask.shape[1]} height={mask.shape[0]} channels=1 foreground_pixels={np.count_nonzero(mask)} foreground_ratio={ratio:.6f} binary=true")

def component_rows(mask, connectivity, min_area):
    count, labels, stats, centroids=cv2.connectedComponentsWithStats(mask, connectivity=connectivity)
    rows=[]
    for label in range(1,count):
        x,y,w,h,area=map(int,stats[label])
        cx,cy=map(float,centroids[label])
        rows.append({"label":label,"area":area,"x":x,"y":y,"width":w,"height":h,"cx":cx,"cy":cy,"kept":area>=min_area})
    return rows, labels

def write_csv(path, rows):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with open(path,"w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["label","area","x","y","width","height","cx","cy","kept"])
        writer.writeheader(); writer.writerows(rows)

def analyze(mask, prefix, connectivity=8, min_area=20, kernel=3, iterations=1):
    if connectivity not in (4,8): raise ValueError("--connectivity aceita somente 4 ou 8")
    if min_area < 0: raise ValueError("--min-area deve ser inteiro não negativo")
    if kernel < 1 or kernel % 2 == 0: raise ValueError("--kernel deve ser ímpar e positivo")
    if iterations < 1: raise ValueError("--iterations deve ser positivo")
    if mask.ndim != 2 or not set(np.unique(mask).tolist()).issubset({0,255}):
        raise ValueError("Entrada de analyze deve ser máscara binária de um canal (0/255)")
    prefix=Path(prefix); prefix.parent.mkdir(parents=True,exist_ok=True)
    initial=mask.copy()
    # Abertura remove pequenos pontos isolados; fechamento pode preencher pequenas falhas.
    element=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(kernel,kernel))
    opened=cv2.morphologyEx(initial,cv2.MORPH_OPEN,element,iterations=iterations)
    final=cv2.morphologyEx(opened,cv2.MORPH_CLOSE,element,iterations=iterations)
    cv2.imwrite(str(prefix)+"_initial.png",initial)
    cv2.imwrite(str(prefix)+"_opening.png",opened)
    cv2.imwrite(str(prefix)+"_final.png",final)
    rows0,_=component_rows(initial,connectivity,0)
    rowsf,labels=component_rows(final,connectivity,min_area)
    # Contagens em ambas conectividades para a máscara inicial
    n4=cv2.connectedComponentsWithStats(initial,connectivity=4)[0]-1
    n8=cv2.connectedComponentsWithStats(initial,connectivity=8)[0]-1
    write_csv(str(prefix)+"_initial.csv",rows0)
    write_csv(str(prefix)+"_final.csv",rowsf)
    colored=np.zeros((*final.shape,3),np.uint8)
    max_label=int(labels.max())
    if max_label:
        colored=cv2.applyColorMap((labels.astype(np.float32)*255/max_label).astype(np.uint8),cv2.COLORMAP_TURBO)
        colored[labels==0]=0
    for r in rowsf:
        x,y,w,h=r["x"],r["y"],r["width"],r["height"]
        cv2.rectangle(colored,(x,y),(x+w-1,y+h-1),(255,255,255),1)
        cv2.putText(colored,str(r["label"]),(x,max(12,y-3)),cv2.FONT_HERSHEY_SIMPLEX,.4,(255,255,255),1)
    cv2.imwrite(str(prefix)+"_labels.png",colored)
    summary={
      "connectivity_final":connectivity,"initial_components_connectivity4":n4,
      "initial_components_connectivity8":n8,"min_area":min_area,
      "morphology":{"order":["opening","closing"],"shape":"ellipse","kernel":[kernel,kernel],"iterations":iterations},
      "initial":{"components_raw":len(rows0),"foreground_pixels":int(np.count_nonzero(initial))},
      "final":{"components_raw":len(rowsf),"components_kept":sum(r["kept"] for r in rowsf),
               "foreground_pixels":int(np.count_nonzero(final)),
               "foreground_pixels_kept":sum(r["area"] for r in rowsf if r["kept"])}
    }
    with open(str(prefix)+"_summary.json","w",encoding="utf-8") as f: json.dump(summary,f,indent=2,ensure_ascii=False)
    print(json.dumps(summary,ensure_ascii=False))
    return summary

def main(argv=None):
    p=argparse.ArgumentParser(prog="pdi_lab",description="Labs M2.1 segmentação e M2.2 componentes/morfologia")
    p.add_argument("--input",required=True); p.add_argument("--output",required=True)
    p.add_argument("--operation",required=True,choices=["segment","analyze"])
    p.add_argument("--method",default="fixed",choices=["fixed","otsu","adaptive","hsv"])
    p.add_argument("--threshold",type=int,default=120); p.add_argument("--invert",action="store_true")
    p.add_argument("--block-size",type=int,default=11); p.add_argument("--c",type=float,default=2)
    p.add_argument("--hsv-lower",type=int,nargs=3); p.add_argument("--hsv-upper",type=int,nargs=3)
    p.add_argument("--connectivity",type=int,default=8); p.add_argument("--min-area",type=int,default=20)
    p.add_argument("--kernel",type=int,default=3); p.add_argument("--iterations",type=int,default=1)
    args=p.parse_args(argv)
    try:
        if args.operation=="segment":
            image=read_image(args.input)
            mask=segment(image,args.method,args.threshold,args.invert,args.block_size,args.c,args.hsv_lower,args.hsv_upper)
            save_mask(mask,args.output)
        else:
            mask=read_image(args.input,grayscale=True)
            analyze(mask,args.output,args.connectivity,args.min_area,args.kernel,args.iterations)
        return 0
    except (ValueError, OSError, cv2.error) as e:
        print(f"ERRO: {e}",file=sys.stderr); return 2
if __name__=="__main__": sys.exit(main())
