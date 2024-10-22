# import cv2
# import numpy as np

# def calculate_center(contours):
#     array_center_x = []
#     array_center_y = []
#     for i in contours: 
#         m = cv2.moments(i)
#         if m['m00'] != 0:
#             cx = int(m['m10']/m['m00'])
#             cy = int(m['m01']/m['m00'])
#             array_center_x.append(cx)
#             array_center_y.append(cy)
#     return (array_center_x, array_center_y)


# def find_bounding_box_frame(gray_frame):
#     ### config noise frame ###
#     ### if no crop system ###
#     # blurred = cv2.GaussianBlur(gray_frame, (85,85), 0)
#     # _, thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#     # kernel = np.ones((300, 300), np.uint8)
#     # thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

#     ### if crop system ###
#     blurred = cv2.GaussianBlur(gray_frame, (5,5), 0)
#     _, thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#     kernel = np.ones((30, 30), np.uint8)
#     thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

#     ### end config noise frame ###
#     contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     return contours, thresh

# def find_bounding_box_light(gray_frame):
#     ### config noise target ###
#     blurred = cv2.GaussianBlur(gray_frame, (55, 55), 0) ## Gaussian blur to reduce noise
#     _, thresh = cv2.threshold(blurred, 180, 255, cv2.THRESH_BINARY)
#     kernel = np.ones((3, 3), np.uint8)
#     thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
#     ### end config noise target ###
#     contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     return contours, thresh

# def main():
#     x_center_light = 0
#     y_center_light = 0
#     x_center_frame = 0
#     y_center_frame = 0

#     # image = cv2.imread('/Users/pcsishun/project_solar_thermal/gui_solar_control/test9.png')
#     # frame = cv2.flip(image, 0)
#     video_path = './test_target.mp4'
#     capture = cv2.VideoCapture(video_path)
#     ret, frame = capture.read()
#     frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
#     ### convert frame to black and white
#     contours_frame, debug_thresh_frame = find_bounding_box_frame(frame_gray)
#     contours_light, debug_thresh_light = find_bounding_box_light(frame_gray)

#     ### find the center of frame ###
#     center_x_light, center_y_light = calculate_center(contours_light)
#     center_x_frame, center_y_frame = calculate_center(contours_frame)

#     ### draw main center of target ###
#     center_color_target = 0
#     for idx,el in  enumerate(center_x_light):
#         cv2.circle(frame, (center_x_light[idx], center_y_light[idx]), 14,(255,0,center_color_target),-1 )
#         cv2.putText(frame, "center_x_light: "+ str(center_x_light[idx]) + " " + "center_y_light: "+str(center_y_light[idx]) ,(center_x_light[idx] - 200, center_y_light[idx] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,center_color_target), 3)
#         center_color_target += 100
#         x_center_light = center_x_light[idx]
#         y_center_light = center_y_light[idx]

#     ### draw main center of frame ###
#     center_color_frame = 0
#     for idx,el in  enumerate(center_x_frame):
#         cv2.circle(frame, (center_x_frame[idx], center_y_frame[idx]), 14,(0,255,center_color_frame),-1 )
#         cv2.putText(frame, "center_x_frame: "+ str(center_x_frame[idx]) + " " + "center_y_frame: "+str(center_y_frame[idx]) ,(center_x_frame[idx], center_y_frame[idx] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,center_color_frame), 3)
#         center_color_frame += 100
#         x_center_frame = center_x_frame[idx]
#         y_center_frame = center_y_frame[idx]

#     ### draw bounding box of target ###
#     area_color_target = 0
#     for cnt in contours_light:
#         x,y,w,h = cv2.boundingRect(cnt)
#         cv2.putText(frame, "X:"+str(x) + " " + "Y:"+str(y) +" "+ "W:"+str(w) +" "+ "H:"+str(h),(x,y+50), cv2.FONT_HERSHEY_SIMPLEX, 1,  (255,0,area_color_target), 4)
#         cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),10)
#         area_color_target += 100

#     ### draw bounding box of frame ###
#     area_color_bounding_box_frame = 0
#     for cnt in contours_frame:
#         x,y,w,h = cv2.boundingRect(cnt)
#         cv2.putText(frame, "X:"+str(x) + " " + "Y:"+str(y) +" "+ "W:"+str(w) +" "+ "H:"+str(h),(x,y+50), cv2.FONT_HERSHEY_SIMPLEX, 1,  (0,255,area_color_bounding_box_frame), 4)
#         cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,area_color_bounding_box_frame),10)
#         area_color_bounding_box_frame += 100

#     ### draw error center ###
#     cv2.putText(frame, "Error_x: " + str(x_center_frame - x_center_light)+"px" + " " + "Error_y: " + str(y_center_frame - y_center_light)+"px" ,(x,h+50), cv2.FONT_HERSHEY_SIMPLEX, 1,  (0,255,255), 4)

#     ### warp all draw in same image frame ### 
#     frame_with_contours = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#     # Displaying the image
#     cv2.imshow("test_image", debug_thresh_light) 
#     cv2.waitKey()
#     cv2.destroyAllWindows()

# main()
