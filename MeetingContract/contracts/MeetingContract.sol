pragma solidity ^0.5.0;


contract MeetingContract {
    struct Meeting {
        string id;
        mapping (address => bool) participants;
        string eventStartHash;
        string eventEndHash;
        mapping (address => bool) approvals;
    }

    address owner;

    Meeting public meeting;

     constructor (string memory id, address[] memory participants) public {
        meeting.id = id;
        for (uint i=0; i< participants.length; i++) {
            meeting.participants[participants[i]] = true;
        }
        owner = msg.sender;
    }

    modifier onlyOwner(){
            require(msg.sender == owner);
            _;
    }

    modifier onlyParticipant(){
            require(meeting.participants[msg.sender]);
            _;
    }

    function getOwner() view public returns(address) {
        return owner;
    }

    function getMeetingId() view public returns(string memory) {
        return (meeting.id);
    }

    function getEvents() view public returns(string memory, string memory) {
        return (meeting.eventStartHash, meeting.eventEndHash);
    }

    function setEvents(string memory start, string memory end) public onlyOwner {
        meeting.eventStartHash = start;
        meeting.eventEndHash = end;
    }

    function approve() public onlyParticipant{
        meeting.approvals[msg.sender] = true;
    }

    function isApproved() view public returns(bool){
        return meeting.approvals[msg.sender];
    }
}
