import numpy as np
from scipy.interpolate import make_interp_spline
import matplotlib.pyplot as plt
import cv2
import copy
import math
 
# change thickness of line by adding 1 to knew set

X_ORIENTATION = 0
Y_ORIENTATION = 1

LEFT = 0
RIGHT = 1

def test_it():

    # Dataset
    x_span = np.array([100, 200, 300, 400])
    y_span = np.array([100, 120, 120, 100])
    
    X_Y_Spline = make_interp_spline(x_span, y_span)
    
    # Returns evenly spaced numbers
    # over a specified interval.
    X_ = np.linspace(x_span.min(), x_span.max(), 500)
    Y_ = X_Y_Spline(X_)


    img = np.ones([500,500,3])
    img *= 255

    X_ = np.round(X_, 0).astype(int)
    Y_ = np.round(Y_, 0).astype(int)

    points = np.stack((X_,Y_)).T
    points = np.unique(points, axis=0)

    for x,y in points:
        img[y,x,0] = 0
        img[y,x,1] = 0
        img[y,x,2] = 0

    img = img / 255

    # cv2.imwrite('color_img.jpg', img)
    cv2.imshow("image", img)
    cv2.waitKey(0)


    print(x_span)
    tri_source = [x_span[3],y_span[3]]


    pt1 = (tri_source[0], tri_source[1]+5)
    pt2 = (tri_source[0]+10, tri_source[1])
    pt3 = (tri_source[0], tri_source[1]-5)

    triangle_cnt = np.array( [pt1, pt2, pt3] )

    cv2.drawContours(img, [triangle_cnt], 0, (0,0,0), -1)

    cv2.imshow("image", img)
    cv2.waitKey(0)



def draw_spline(img,x_span,y_span,thickness,orientation):

    
    X_Y_Spline = make_interp_spline(x_span, y_span)
    
    # Returns evenly spaced numbers
    # over a specified interval.
    X_ = np.linspace(x_span.min(), x_span.max(), 500)
    Y_ = X_Y_Spline(X_)
    
    X_ = np.round(X_, 0).astype(int)
    Y_ = np.round(Y_, 0).astype(int)

    base_points = np.stack((X_,Y_)).T
    base_points = np.unique(base_points, axis=0)

    base_points_shape = base_points.shape
    print(base_points_shape)

    lag = 10
    if orientation is X_ORIENTATION:
        for x,y in base_points:
            img = cv2.circle(img, (x,y), thickness, (0,0,0), -1)
        base_points_y = base_points[:,1]
        y_max_idx = base_points_y.shape[0] - 1
        end_slope = (base_points_y[y_max_idx] - base_points_y[y_max_idx-lag])*-1
        print("end point")
        print(base_points_y[y_max_idx])

        print("lag point")
        print(base_points_y[y_max_idx-lag])
    else:
        for x,y in base_points:
            img = cv2.circle(img, (y,x), thickness, (0,0,0), -1)
        
        # get slope estimate from last point and 10 points back
        base_points_x = base_points[:,0]
        x_max_idx = base_points_x.shape[0] - 1
        end_slope = (base_points_x[x_max_idx] - base_points_x[x_max_idx-lag])*-1
        print("end point")
        print(base_points_x[x_max_idx])

        print("lag point")
        print(base_points_x[x_max_idx-lag])

    

    

    

    return img, end_slope


def draw_arrowhead(img,x_span,y_span,tip_slope,arrow_pos,orientation):

    lag = 10
    tip_len = 5
    base_len = 5


    # TODO:: small slope makes 10 lag used above to get slope estimate drift
    # i.e. lengths for base and tip are scaled less when slope is large 
    # can adjust slope estimate to fix or set slope threshold for changing angle (prob need to change slope estimate to work for different angles)
    # slope == 1 => deg == 45

    if arrow_pos == RIGHT:
        if orientation == X_ORIENTATION:
            tri_source = [x_span[3],y_span[3]]
        else:
            tri_source = [y_span[3],x_span[3]]
    else:
        if orientation == X_ORIENTATION:
            tri_source = [x_span[0],y_span[0]]
        else:
            tri_source = [y_span[0],x_span[0]]

        # flip slope
        tip_slope *= -1

    # img = cv2.circle(img, tuple(tri_source), 3, (0,255,0), -1)

    if abs(tip_slope) < 2:

        if arrow_pos == RIGHT:
            pt1 = (tri_source[0], tri_source[1]+base_len)
            pt2 = (tri_source[0]+tip_len, tri_source[1])
            pt3 = (tri_source[0], tri_source[1]-base_len)
        else:
            pt1 = (tri_source[0], tri_source[1]-base_len)
            pt2 = (tri_source[0]-tip_len, tri_source[1])
            pt3 = (tri_source[0], tri_source[1]+base_len)

        triangle_cnt = np.array( [pt1, pt2, pt3] )

        cv2.drawContours(img, [triangle_cnt], 0, (0,0,0), -1)

    else:

        # arrow base slope is just negative reciprocal
        arrowhead_base_slpe = -1/tip_slope

        # returned in radians
        # get angle from slope in right triangle drawn by slopes of tip and base
        tip_deg = math.atan(tip_slope)
        base_deg = math.atan(arrowhead_base_slpe)

        print("slope")
        print(tip_slope)
        print("deg")
        print(tip_deg)


        # not really lag # pixels, since use unique op
        # get location of arrowhead tip point w/ law of sines and similar triangles
        tip_rise = tip_len * math.sin(tip_deg)
        tip_run = (lag * tip_rise) / tip_slope
        tip_rise = math.floor(tip_rise)
        tip_run = math.floor(tip_run)


        print("tip rise run")
        print(tip_rise)
        print(tip_run)

        
        
        # get location of arrowhead base points w/ law of sines and similar triangles
        base_rise = base_len * math.sin(base_deg)
        base_run = (lag * base_rise) / tip_slope
        base_rise = math.floor(base_rise)
        base_run = math.floor(base_run)

        if arrow_pos == RIGHT:
            pt1 = (tri_source[0]-base_rise, tri_source[1]-base_run)
            pt2 = (tri_source[0]+tip_run, tri_source[1]-tip_rise)
            pt3 = (tri_source[0]+base_rise, tri_source[1]+base_run)
        else:
            pt1 = (tri_source[0]+base_rise, tri_source[1]+base_run)
            pt2 = (tri_source[0]-tip_run, tri_source[1]+tip_rise)
            pt3 = (tri_source[0]-base_rise, tri_source[1]-base_run)

        triangle_cnt = np.array( [pt1, pt2, pt3] )

        cv2.drawContours(img, [triangle_cnt], 0, (0,0,0), -1)

        # img = cv2.circle(img, pt2, 3, (0,0,255), -1)
        # img = cv2.circle(img, pt1, 3, (255,0,0), -1)
        # img = cv2.circle(img, pt3, 3, (255,0,0), -1)


    return img


def test_textbox():

    img = np.ones([500,500,3])
    img *= 255

    x1 = 150
    y1 = 150

    color = (30,255,0)
    text_color = (0,0,0)

    label = "testing label asdf asdf asdf asdf "
    
    # For the text background
    # Finds space required by the text so that we can put a background with that amount of width.
    (w, h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)

    # Prints the text.    
    # to add boarder just do same rectangle but don't fill and can just make it to include optionally
    img = cv2.rectangle(img, (x1, y1), (x1 + w + 20, y1 + h + 20), color, -1)
    img = cv2.rectangle(img, (x1, y1), (x1 + w + 20, y1 + h + 20), (0,0,0), 1)
    img = cv2.putText(img, label, (x1 + 10, y1 + h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)

    # img = img / 255
    cv2.imshow("image", img, )
    cv2.waitKey(0)

def draw_textbox(img,label,location):

    x1,y1 = location

    color = (30,255,0)
    text_color = (0,0,0)
    
    # For the text background
    # Finds space required by the text so that we can put a background with that amount of width.
    (w, h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)

    # Prints the text.    
    # to add boarder just do same rectangle but don't fill and can just make it to include optionally
    img = cv2.rectangle(img, (x1, y1), (x1 + w + 20, y1 + h + 20), color, -1)
    img = cv2.rectangle(img, (x1, y1), (x1 + w + 20, y1 + h + 20), (0,0,0), 1)
    img = cv2.putText(img, label, (x1 + 10, y1 + h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)

    # img = img / 255
    cv2.imshow("image", img, )
    cv2.waitKey(0)


def test_relationship():

    img = np.ones([400,700,3])
    img *= 255


    draw_textbox(img,"PI3K",[100,100])
    draw_textbox(img,"AKTPxGAMMA",[520,100])

    # Dataset
    x_span = np.array([200, 300, 400, 500])
    y_span = np.array([110, 90, 90, 110])

    thickness = 1
    img, end_slope = draw_spline(img,x_span,y_span,thickness,X_ORIENTATION)
    img = draw_arrowhead(img,x_span,y_span,end_slope,LEFT,X_ORIENTATION)

    cv2.imshow("image", img, )
    cv2.waitKey(0)



if __name__ == "__main__":

    # img = np.ones([500,500,3])
    # img *= 255


    # # Dataset
    # x_span = np.array([100, 200, 300, 400])
    # y_span = np.array([100, 80, 80, 100])

    # # TODO:: remove orientation code and adjust to be more flexible

    # thickness = 1
    # img, end_slope = draw_spline(img,x_span,y_span,thickness,X_ORIENTATION)
    # img = draw_arrowhead(img,x_span,y_span,end_slope,RIGHT,X_ORIENTATION)


    # img = img / 255
    # cv2.imshow("image", img, )
    # cv2.waitKey(0)




    # img = np.ones([500,500,3])
    # img *= 255
    # label = "PCI3"
    # location = [150,150]

    # draw_textbox(img,label,location)


    test_relationship()