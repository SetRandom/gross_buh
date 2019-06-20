from ..modules.checker_fns import generate_check, API_URL
import datetime
from hypothesis import given
from hypothesis.strategies import datetimes, integers, floats


def test_generate_check():
    test_s = "t=20190325T200700&s=196.19&fn=8716000100001094&i=170196&fp=1990566828&n=1"
    success_result = (
        'https://proverkacheka.nalog.ru:9999/v1/inns/*/kkts/*/fss/8716000100001094/tickets/170196?fiscalSign=1990566828&sendToEmail=no',
        'https://proverkacheka.nalog.ru:9999/v1/ofds/*/inns/*/fss/8716000100001094/operations/1/tickets/170196?fiscalSign=1990566828&date=2019-03-25T20:07:00&sum=19619',
        datetime.datetime(2019, 3, 25, 20, 7))
    assert generate_check(test_s) == success_result


@given(datetimes(min_value=datetime.datetime(2018, 1, 1, 1, 1),
                 max_value=datetime.datetime(2999, 12, 31)),
       floats(),
       integers(min_value=1000000000000000,
                max_value=9999999999999999),
       integers(),
       integers())
def test_generate_check_any_data(date, summ, fn, i, fp):
    date = date.replace(microsecond=0).replace(second=0)
    pass_s = f"t={date.strftime('%Y%m%dT%H%M')}&s={summ}&fn={fn}&i={i}&fp={fp}&n=1"
    summ = f'{summ}'.replace(".", "")
    success_result = (
        f'{API_URL}/v1/inns/*/kkts/*/fss/{fn}/tickets/{i}?fiscalSign={fp}&sendToEmail=no',
        f'{API_URL}/v1/ofds/*/inns/*/fss/{fn}/operations/1/tickets/{i}?fiscalSign={fp}&date={date.isoformat()}&sum={summ}',
        date)
    assert generate_check(pass_s) == success_result
