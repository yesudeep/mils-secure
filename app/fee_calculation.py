

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
        Fee(6000, 15),
        Fee(5000, 30),
        Fee(3000, 40),
    ]
    assert calculate_fee(fees, 0) == 6000
    assert calculate_fee(fees, 1) == 6000
    assert calculate_fee(fees, 2) == 6000
    assert calculate_fee(fees, 3) == 6000
    assert calculate_fee(fees, 4) == 6000
    assert calculate_fee(fees, 5) == 6000
    assert calculate_fee(fees, 6) == 6000
    assert calculate_fee(fees, 7) == 6000
    assert calculate_fee(fees, 8) == 6000
    assert calculate_fee(fees, 9) == 6000
    assert calculate_fee(fees, 10) == 6000
    assert calculate_fee(fees, 11) == 6000
    assert calculate_fee(fees, 12) == 6000
    assert calculate_fee(fees, 13) == 6000
    assert calculate_fee(fees, 14) == 6000
    assert calculate_fee(fees, 15) == 6000
    assert calculate_fee(fees, 16) == 6000
    assert calculate_fee(fees, 17) == 6000
    assert calculate_fee(fees, 18) == 6000
    assert calculate_fee(fees, 19) == 6000
    assert calculate_fee(fees, 20) == 6000
    assert calculate_fee(fees, 21) == 6000
    assert calculate_fee(fees, 22) == 6000
    assert calculate_fee(fees, 23) == 6000
    assert calculate_fee(fees, 24) == 6000
    assert calculate_fee(fees, 25) == 6000
    assert calculate_fee(fees, 26) == 6000
    assert calculate_fee(fees, 27) == 6000
    assert calculate_fee(fees, 28) == 6000
    assert calculate_fee(fees, 29) == 6000
    assert calculate_fee(fees, 30) == 5000
    assert calculate_fee(fees, 31) == 5000
    assert calculate_fee(fees, 32) == 5000
    assert calculate_fee(fees, 33) == 5000
    assert calculate_fee(fees, 34) == 5000
    assert calculate_fee(fees, 35) == 5000
    assert calculate_fee(fees, 36) == 5000
    assert calculate_fee(fees, 37) == 5000
    assert calculate_fee(fees, 38) == 5000
    assert calculate_fee(fees, 39) == 5000
    assert calculate_fee(fees, 40) == 3000
    assert calculate_fee(fees, 41) == 3000
    assert calculate_fee(fees, 42) == 3000
    assert calculate_fee(fees, 43) == 3000
    assert calculate_fee(fees, 44) == 3000
    assert calculate_fee(fees, 45) == 3000
    assert calculate_fee(fees, 46) == 3000
    assert calculate_fee(fees, 47) == 3000
    assert calculate_fee(fees, 48) == 3000
    assert calculate_fee(fees, 49) == 3000
    assert calculate_fee(fees, 50) == 3000
    print "all tests passed"

