import numpy as np
from numpy.lib.npyio import save
from scipy.interpolate import make_interp_spline
import matplotlib.pyplot as plt
from scipy import interpolate
import cv2
import copy
import math

from scipy.sparse import base
 
# change thickness of line by adding 1 to knew set

X_ORIENTATION = 0
Y_ORIENTATION = 1

START = 0
END = 1

UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

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

def check_orientation(source_point,comparison_pt):

    # check orientation
    if abs(source_point[0] - comparison_pt[0]) > abs(source_point[1] - comparison_pt[1]):
        # LEFT or RIGHT
        if source_point[0] - comparison_pt[0] > 0:
            orientation = RIGHT
        else:
            orientation = LEFT
    else:
        # UP or DOWN
        if source_point[1] - comparison_pt[1] > 0:
            orientation = DOWN
        else:
            orientation = UP

    return orientation

def draw_spline(img,x_span,y_span,thickness,arrow_placement):


    param = np.linspace(0, 1, x_span.size)
    # clever way to break it up to avoid 1st param no duplicate error
    # make linespace to serve as first param and interpolating the target values which is the set of x & y values
    spl = make_interp_spline(param, np.c_[x_span,y_span], k=3) #(1)
    # TODO:: change 500 parameter to be dynamic based on manitude differences in x_span
    X_, Y_ = spl(np.linspace(0, 1, x_span.size * 500)).T #(2)

    
    X_ = np.round(X_, 0).astype(int)
    Y_ = np.round(Y_, 0).astype(int)

    base_points = np.stack((X_,Y_)).T
    base_points = np.unique(base_points, axis=0)

    # print(base_points)

    base_points_shape = base_points.shape
    print(base_points_shape)

    lag = 10
    # TODO:: dynamically adjust lag length based on # samples here or change how selecting comparison point

    # draw spline
    for x,y in base_points:
        img = cv2.circle(img, (x,y), thickness, (0,0,0), -1)  


    tmp_len = x_span.size
    print('temp len')
    print(tmp_len)

    # get reference point
    if arrow_placement == END:
        source_point = [x_span[tmp_len-1],y_span[tmp_len-1]]
    else:
        source_point = [x_span[0],y_span[0]]

    # select distinct and nth closest
    # TODO:: make so don't have to loop through all points
    max_idx = base_points.shape[0] - 1
    comparison_pt = None
    dist = 50
    candidate_points = []
    candidate_dists = []
    for idx in range(0,max_idx-1,1):
        if base_points[idx,0] != source_point[0] and base_points[idx,1] != source_point[1]:
            tmp_dist = math.dist(base_points[idx], source_point)
            if tmp_dist < dist:
                candidate_points.append(base_points[idx])
                candidate_dists.append(tmp_dist)

    if len(candidate_dists) >= lag:
        candidate_dists = np.array(candidate_dists)
        candidate_idxs = np.argsort(candidate_dists)
        comparison_pt = candidate_points[candidate_idxs[lag]]

    # check if slope of line is too big or too small to rule out
    if comparison_pt is None:
        if arrow_placement == END:
            comparison_pt = base_points[0]
        else:
            comparison_pt = base_points[max_idx-1]

    x1 = source_point[0]
    x2 = comparison_pt[0]
    y1 = source_point[1]
    y2 = comparison_pt[1]

    orientation = check_orientation(source_point,comparison_pt)
                
    f=(y2-y1)/(x2-x1)*-1


    # f = interpolate.interp1d(sample_xs, sample_ys, fill_value='extrapolate')

    # img = cv2.circle(img, tuple([int(source_point[0]),int(source_point[1])]), 3, (0,255,0), -1)
    # img = cv2.circle(img, tuple([int(comparison_pt[0]),int(comparison_pt[1])]), 3, (0,0,255), -1)

    return img, f, orientation


def draw_arrowhead(img,x_span,y_span,tip_slope,arrow_pos,arrow_orientation,tip_len,base_len):

    # get reference point
    if arrow_pos == END:
        tri_source = [x_span[3],y_span[3]]
    else:
        tri_source = [x_span[0],y_span[0]]

    # img = cv2.circle(img, tuple(tri_source), 3, (40,255,0), -1)

    print('tip_slope')
    print(tip_slope)

    if abs(tip_slope) > 10 or abs(tip_slope) < 1:

        if arrow_orientation == UP:
            pt1 = (tri_source[0]-base_len, tri_source[1])
            pt2 = (tri_source[0], tri_source[1]-tip_len)
            pt3 = (tri_source[0]+base_len, tri_source[1])
        elif arrow_orientation == DOWN:
            pt1 = (tri_source[0]+base_len, tri_source[1])
            pt2 = (tri_source[0], tri_source[1]+tip_len)
            pt3 = (tri_source[0]-base_len, tri_source[1])
        elif arrow_orientation == LEFT:
            pt1 = (tri_source[0], tri_source[1]-base_len)
            pt2 = (tri_source[0]-tip_len, tri_source[1])
            pt3 = (tri_source[0], tri_source[1]+base_len)
        else:
            pt1 = (tri_source[0], tri_source[1]+base_len)
            pt2 = (tri_source[0]+tip_len, tri_source[1])
            pt3 = (tri_source[0], tri_source[1]-base_len)

        triangle_cnt = np.array( [pt1, pt2, pt3] )

        cv2.drawContours(img, [triangle_cnt], 0, (0,0,0), -1)

    else:

        # arrow base slope is just negative reciprocal
        arrowhead_base_slpe = -1/tip_slope

        print("arrowhead_base_slpe")
        print(arrowhead_base_slpe)

        # returned in radians
        # get angle from slope in right triangle drawn by slopes of tip and base
        tip_deg = math.atan(tip_slope)
        base_deg = math.atan(arrowhead_base_slpe)

        print('tip rad')
        print(math.sin(tip_deg))
        print('base rad')
        print(math.sin(base_deg))



        # get location of arrowhead tip point w/ law of sines and similar triangles
        tip_rise = tip_len * math.sin(tip_deg)
        tip_run = tip_rise / tip_slope
        tip_rise = math.floor(tip_rise)
        tip_run = math.floor(tip_run)

        # get location of arrowhead base points w/ law of sines and similar triangles
        if arrow_orientation == RIGHT or arrow_orientation == LEFT:
            base_rise = (base_len * math.sin(base_deg))
            base_run = base_rise / arrowhead_base_slpe
            base_rise = math.floor(base_rise)
            base_run = math.floor(base_run)
        else:
            # use similar triangles for run instead of pythogorean to avoid sign issues
            base_rise = base_len * math.sin(base_deg)
            base_run = base_rise / arrowhead_base_slpe
            base_rise = math.floor(base_rise)
            base_run = math.floor(base_run)



        print("tip rise run")
        print(tip_rise)
        print(tip_run)

        print("base rise run")
        print(base_rise)
        print(base_run)

        print('orientation')
        print(arrow_orientation)

        if arrow_orientation == RIGHT:
            pt1 = (tri_source[0]-base_rise, tri_source[1]-base_run)
            pt2 = (tri_source[0]+tip_run, tri_source[1]-tip_rise)
            pt3 = (tri_source[0]+base_rise, tri_source[1]+base_run)
        elif arrow_orientation == LEFT:
            pt1 = (tri_source[0]+base_rise, tri_source[1]+base_run)
            pt2 = (tri_source[0]-tip_run, tri_source[1]+tip_rise)
            pt3 = (tri_source[0]-base_rise, tri_source[1]-base_run)
        elif arrow_orientation == DOWN:

            # adjust tip_run & tip_rise for positive or negative slope
            if tip_rise < 0:
                tip_rise *= -1
                tip_run *= -1
            pt1 = (tri_source[0]-base_run, tri_source[1]+base_rise)
            pt2 = (tri_source[0]-tip_run, tri_source[1]+tip_rise)
            pt3 = (tri_source[0]+base_run, tri_source[1]-base_rise)
        elif arrow_orientation == UP:
            # adjust tip_run & tip_rise for positive or negative slope on UP arrow
            # don't have to adjust base_rise & base_run for since pt1 and pt3 just flip
            if tip_rise > 0:
                tip_rise *= -1
                tip_run *= -1
            pt1 = (tri_source[0]-base_run, tri_source[1]+base_rise)
            pt2 = (tri_source[0]-tip_run, tri_source[1]+tip_rise)
            pt3 = (tri_source[0]+base_run, tri_source[1]-base_rise)



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
    y_span = np.array([130, 150, 150, 130])

    thickness = 1
    tip_len = 10
    base_len = 50
    img, f, orientation = draw_spline(img,x_span,y_span,thickness,END)
    img = draw_arrowhead(img,x_span,y_span,f,END,orientation,tip_len,base_len)

    # img = img / 255
    cv2.imshow("image", img, )
    cv2.waitKey(0)


def draw_relationship(img,thickness,tip_len,base_len,arrow_pos,entity1_pos,entity2_pos):
    
    draw_textbox(img,"PI3K",entity1_pos)
    draw_textbox(img,"AKTPxGAMMA",entity2_pos)

    # Dataset
    # TODO:: set this dynamically based on location of entities
    # TODO:: set up to be several different classes of splines

    # TODO:: first is evenly sampled line

    anchor_points = np.linspace(entity1_pos, entity2_pos, num=4)
    print(anchor_points)
    # x_span = anchor_points[:,0]
    # y_span = anchor_points[:,1]
    # # print(tmp_x)
    # # print(tmp_y)

    # y_span[1] += 30

    # print(x_span)
    # print(y_span)

    

    y_span = np.array([200, 300, 350, 500])
    x_span = np.array([100, 150, 150, 100])

    img, f, orientation = draw_spline(img,x_span,y_span,thickness,END)
    img = draw_arrowhead(img,x_span,y_span,f,END,orientation,tip_len,base_len)

    return img


if __name__ == "__main__":

    # img = np.ones([500,500,3])
    # img *= 255


    # # Dataset
    # x_span = np.array([100, 200, 300, 400])
    # y_span = np.array([100, 150, 150, 100])

    # thickness = 1
    # img, f, orientation = draw_spline(img,x_span,y_span,thickness,START)
    # img = draw_arrowhead(img,x_span,y_span,f,START,orientation)


    # img = img / 255
    # cv2.imshow("image", img, )
    # cv2.waitKey(0)


    img = np.ones([600,700,3])
    img *= 255

    thickness = 1
    tip_len = 10
    base_len = 10
    arrow_pos = END
    entity1_pos = [100,100]
    entity2_pos = [520,100]
    img = draw_relationship(img,thickness,tip_len,base_len,arrow_pos,entity1_pos,entity2_pos)

    cv2.imshow("image", img, )
    cv2.waitKey(0)




    # img = np.ones([500,500,3])
    # img *= 255
    # label = "PCI3"
    # location = [150,150]

    # draw_textbox(img,label,location)


    # test_relationship()





    # list1 = np.array([100, 100, 300, 400])
    # list2 = np.array([100, 80, 80, 100])

    # x = np.array(list1)
    # y = np.array(list2)

    # param = np.linspace(0, 1, x.size)
    # # clever way to break it up to avoid 1st param no duplicate error
    # # make linespace to serve as first param and interpolating the target values which is the set of x & y values
    # spl = make_interp_spline(param, np.c_[x,y], k=3) #(1)
    # xnew, y_smooth = spl(np.linspace(0, 1, x.size * 100)).T #(2)
    # plt.plot(xnew, y_smooth)
    # plt.scatter(x, y, c="r")
    # plt.show()