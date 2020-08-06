# Thanks to:
# https://wiki.archlinux.org/index.php/Calibrating_Touchscreen#Calculate_the_Coordinate_Transformation_Matrix
#
#
# You need to shrink your touch area into a rectangle which is smaller than the
# total screen. This means, you have to know four values:

# - Height of touch area.
# - Width of touch area.
# - Horizontal offset (x offset): amount of pixels between the left edge of
#   your total screen and the left edge of your touch area.
# - Vertical offset (y offset): amount of pixels between the top edge of your
#   total screen and the top edge of your touch area.
#
#
#   xinput map-to-output 19 HDMI-0

device = 'Tablet Monitor Pen Pen (0)'

total_height = 1080 * 2
total_width = 1920 * 2

touch_area_width = 1920
touch_area_height = 1080
touch_area_x_offset = 1920
touch_area_y_offset = 1080

c0 = touch_area_width / total_width
c2 = touch_area_height / total_height
c1 = touch_area_x_offset / total_width
c3 = touch_area_y_offset / total_height

cmatrix = [
    [c0, 0, c1],
    [0, c2, c3],
    [0, 0, 1],
]

prop = (
    ' '.join(' '.join(str(column) for column in row) for row in cmatrix)
)

print(
    'xinput set-prop "{}" --type=float '
    '"Coordinate Transformation Matrix" {}'.format(
        device,
        prop,
    )
)
