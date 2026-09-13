def test_profile_str(profile):
    """Test the profile model string representation"""
    assert str(profile) == f"{profile.user.username}'s Profile"
