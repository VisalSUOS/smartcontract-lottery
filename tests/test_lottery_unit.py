# 0.019
# 190000000000000000
from operator import index
import pytest
from brownie import Lottery, accounts, config, network, exceptions
from web3 import Web3
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    fund_with_link,
    get_account,
    get_contract,
)


def skip_test_if_not_local_network():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()


def test_get_entrance_fee():
    # Arrange
    skip_test_if_not_local_network()
    lottery = deploy_lottery()
    # Act
    # 2,000 eth / usd
    # usdEntryFee is 50
    # 2000/1 = 50/x == 0.025
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    entrance_fee = lottery.getEntranceFee()
    # Assert
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_starter():
    # Arrange
    skip_test_if_not_local_network()
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # Arrange
    skip_test_if_not_local_network()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # Act
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    # Arrange
    skip_test_if_not_local_network()
    lottery = deploy_lottery()
    account = get_account()
    entrance_fee = lottery.getEntranceFee()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": entrance_fee})
    lottery.enter({"from": account, "value": entrance_fee})
    lottery.enter({"from": account, "value": entrance_fee})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    assert lottery.lottery_state() == 2


def test_can_pick_winner():
    skip_test_if_not_local_network()
    lottery = deploy_lottery()
    account = get_account()
    entrance_fee = lottery.getEntranceFee()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": entrance_fee})
    lottery.enter({"from": get_account(index=1), "value": entrance_fee})
    lottery.enter({"from": get_account(index=2), "value": entrance_fee})
    fund_with_link(lottery)
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    # 777 % 3 = 0
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery


# def test_get_entrance_fee():
#     account = accounts[0]
#     lottery = Lottery.deploy(
#         config["networks"][network.show_active()]["eth_usd_price_feed"],
#         {"from": account},
#     )
#     assert lottery.getEntranceFee() > Web3.toWei(0.018, "ether")
#     assert lottery.getEntranceFee() < Web3.toWei(0.022, "ether")
