

# for count less than 5
#     3000
# for count less than 10 but greater than or equal to 5
#     2000
# for count greater than or equal to 10
#     1000
def calculate_fee(fees_sorted_by_count, count):
    fees = fees_sorted_by_count
    final_fee = fees[0].fee
    for f in fees:
        if count >= f.for_participant_count:
            final_fee = f.fee
    return final_fee

if __name__ == "__main__":
    class Fee(object):
        def __init__(self, fee, for_participant_count):
            self.fee = fee
            self.for_participant_count = for_participant_count
    fees = [
        Fee(3000, 1),
        Fee(2000, 5),
        Fee(1000, 10),
    ]
    assert calculate_fee(fees, 0) == 3000
    assert calculate_fee(fees, 1) == 3000
    assert calculate_fee(fees, 2) == 3000
    assert calculate_fee(fees, 3) == 3000
    assert calculate_fee(fees, 4) == 3000
    assert calculate_fee(fees, 5) == 2000
    assert calculate_fee(fees, 6) == 2000
    assert calculate_fee(fees, 7) == 2000
    assert calculate_fee(fees, 8) == 2000
    assert calculate_fee(fees, 9) == 2000
    assert calculate_fee(fees, 10) == 1000
    assert calculate_fee(fees, 11) == 1000
    assert calculate_fee(fees, 12) == 1000
    print "all tests passed"

