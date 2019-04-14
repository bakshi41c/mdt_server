const MeetingContract = artifacts.require('MeetingContract');

contract('MeetingContract', function(accounts) {

  it('getOwner() gets the owner', async () => {
    const contract = await MeetingContract.deployed();
    const creator = await contract.getOwner();
    assert.equal(creator, accounts[0], 'main account is the creator')
  })

  it('getting correct meeting id', async () => {
    const contract = await MeetingContract.deployed();
    const message = await contract.getMeetingId();
    assert.equal(message, 'meetingId', 'meeting id is correct')
  })

  it('setting and getting event hashes', async () => {
    const contract = await MeetingContract.deployed();
    await contract.setEvents('start_event_hash', 'end_event_hash');
    const results = await contract.getEvents();
    assert.equal(results[0], 'start_event_hash', 'start event is correct')
    assert.equal(results[1], 'end_event_hash', 'end event is correct')
  })

  it('non participant approving throws error', async () => {
    const contract = await MeetingContract.deployed();
    try {
        await contract.approve()
    } catch (error) {
        err = error
    }
    assert.ok(err instanceof Error)
  })
})