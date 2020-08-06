class DomainMapper:

    def __init__(self, from_domain, to_domain):
        self._from_domain = from_low, from_high = from_domain
        self._to_domain = to_low, to_high = to_domain
        self._slope = (to_high - to_low) / (from_high - from_low)

    def map(self, value):
        from_low, _ = self._from_domain
        to_low, _ = self._to_domain

        return (value - from_low) * self._slope + to_low


class LinearCoordinatesMapper:

    def __init__(
        self, from_dimensions, to_dimensions,
        padding=(0, 0, 0, 0),
    ):
        self._from_dimensions = from_w, from_h = from_dimensions
        self._to_dimensions = to_w, to_h = to_dimensions
        self._padding = top, right, bottom, left = padding

        self._x_mapper = DomainMapper(
            (0, from_w),
            (left, to_w - right),
        )
        self._y_mapper = DomainMapper(
            (0, from_h),
            (top, to_h - bottom),
        )

    def map(self, x, y):
        return (
            self._x_mapper.map(x),
            self._y_mapper.map(y),
        )


class RatioCoordinatesMapper:

    def __init__(
        self, from_dimensions, to_dimensions,
        padding=(0, 0, 0, 0),
        center=True,
    ):
        self._from_dimensions = from_w, from_h = from_dimensions
        self._to_dimensions = to_w, to_h = to_dimensions
        self._padding = top, right, bottom, left = padding

        ratio = min(
            to_w / from_w,
            to_h / from_h,
        )

        to_max_w, to_max_h = (
            from_w * ratio,
            from_h * ratio,
        )

        to_min_w, to_min_h = 0, 0

        if center:
            to_min_w, to_min_h = (
                (to_w - to_max_w) / 2,
                (to_h - to_max_h) / 2,
            )

        self._x_mapper = DomainMapper(
            (0, from_w),
            (to_min_w + left, to_min_w + to_max_w - right),
        )
        self._y_mapper = DomainMapper(
            (0, from_h),
            (to_min_h + top, to_min_h + to_max_h - bottom),
        )

    def map(self, x, y):
        return (
            self._x_mapper.map(x),
            self._y_mapper.map(y),
        )


__all__ = [
    'DomainMapper',
    'LinearCoordinatesMapper',
    'RatioCoordinatesMapper',
]
