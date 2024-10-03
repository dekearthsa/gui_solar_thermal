import cv2
import numpy as np

def calculate_center(contours):
    array_center_x = []
    array_center_y = []
    for i in contours: 
        m = cv2.moments(i)
        if m['m00'] != 0:
            cx = int(m['m10']/m['m00'])
            cy = int(m['m01']/m['m00'])
            array_center_x.append(cx)
            array_center_y.append(cy)
    return (array_center_x, array_center_y)

def main():
    image = cv2.imread('/Users/pcsishun/project_solar_thermal/gui_solar_control/test.png')
    frame = cv2.flip(image, 0)
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    blurred = cv2.GaussianBlur(frame_gray, (25, 25), 0) ## Gaussian blur to reduce noise
    _, thresh = cv2.threshold(blurred, 201, 255, cv2.THRESH_BINARY  + cv2.THRESH_OTSU)

    # Erosion to remove small white noise, dilation to close gaps
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    center_x, center_y = calculate_center(contours)

    cnt = contours[0]
    area = cv2.contourArea(cnt)
    perimeter = cv2.arcLength(cnt,True)
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect)
    box = np.intp(box)

    x,y,w,h = cv2.boundingRect(cnt)

    center_color = 0
    for idx,el in  enumerate(center_x):
        ### draw main center of target ###
        if idx != 0:

            center_color += 50
            cv2.circle(frame, (center_x[idx], center_y[idx]), 14,(0,255,center_color),-1 )
            cv2.putText(frame, "center_x: "+ str(center_x[idx]) + " " + "center_y: "+str(center_y[idx]) ,(center_x[idx], center_y[idx] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (center_color,0,0), 3)

    center_color = 0
    for cnt in contours:
        center_color += 50
        x,y,w,h = cv2.boundingRect(cnt)
        cv2.putText(frame, "X:"+str(x) + " " + "Y:"+str(y) +" "+ "W:"+str(w) +" "+ "H:"+str(h),(x,h), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,center_color), 4)

    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)
    cv2.drawContours(frame,[box],0,(0,0,255),10)

    ### warp all draw in same image frame ### 
    frame_with_contours = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Displaying the image
    cv2.imshow("test_image", frame_with_contours) 
    cv2.waitKey()
    cv2.destroyAllWindows()


main()