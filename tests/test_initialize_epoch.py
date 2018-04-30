# ensure that our fixture 'new_epoch' functions properly
def test_new_epoch(casper_chain, casper, new_epoch):
    for _ in range(4):
        prev_epoch = casper.current_epoch()
        prev_block_number = casper_chain.head_state.block_number
        expected_jump = casper.EPOCH_LENGTH() - (prev_block_number % casper.EPOCH_LENGTH())

        new_epoch()

        assert casper.current_epoch() == prev_epoch + 1
        assert casper_chain.head_state.block_number == prev_block_number + expected_jump


def test_checkpoint_hashes(casper_chain, casper, new_epoch):
    for _ in range(4):
        next_epoch = casper.current_epoch() + 1
        epoch_length = casper.EPOCH_LENGTH()

        casper_chain.mine(epoch_length * next_epoch - casper_chain.head_state.block_number)

        casper.initialize_epoch(next_epoch)
        current_epoch = casper.current_epoch()
        # This hash is actually off because our current setup requires us
        # to mine the block before the call to `initialize_epoch`.
        # If this were actually a CALL before the block was process as specified in the EIP
        # Then the expected hash would be of the prev_block (`get_block_hash(1)`)
        expected_hash = casper_chain.head_state.get_block_hash(0)

        assert current_epoch == next_epoch
        assert casper.checkpoint_hashes(current_epoch) == expected_hash


def test_checkpoint_deposits(casper_chain, casper, funded_privkeys, deposit_amount,
                             induct_validator, deposit_validator, new_epoch,
                             mk_suggested_vote):
    current_epoch = casper.current_epoch()
    assert casper.checkpoints__cur_dyn_deposits(current_epoch) == 0
    assert casper.checkpoints__prev_dyn_deposits(current_epoch) == 0

    new_epoch()
    current_epoch = casper.current_epoch()

    assert casper.checkpoints__cur_dyn_deposits(current_epoch) == 0
    assert casper.checkpoints__prev_dyn_deposits(current_epoch) == 0

    initial_validator = deposit_validator(funded_privkeys[0], deposit_amount)

    new_epoch()
    current_epoch = casper.current_epoch()

    assert casper.checkpoints__cur_dyn_deposits(current_epoch) == 0
    assert casper.checkpoints__prev_dyn_deposits(current_epoch) == 0

    new_epoch()
    current_epoch = casper.current_epoch()

    # checkpoints are for the lost block in the previous epoch
    # so checkpoint dynasty totals should lag behind
    assert casper.total_curdyn_deposits_scaled() == deposit_amount
    assert casper.total_prevdyn_deposits_scaled() == 0
    assert casper.checkpoints__cur_dyn_deposits(current_epoch) == 0
    assert casper.checkpoints__prev_dyn_deposits(current_epoch) == 0

    casper.vote(mk_suggested_vote(initial_validator, funded_privkeys[0]))
    new_epoch()
    current_epoch = casper.current_epoch()

    assert casper.total_curdyn_deposits_scaled() == deposit_amount
    assert casper.total_prevdyn_deposits_scaled() == deposit_amount
    assert casper.checkpoints__cur_dyn_deposits(current_epoch) == deposit_amount
    assert casper.checkpoints__prev_dyn_deposits(current_epoch) == 0

 
