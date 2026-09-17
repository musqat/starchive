class User {
  const User({required this.id, required this.email, required this.nickname});

  final int id;
  final String email;
  final String nickname;

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      email: json['email'] as String,
      nickname: json['nickname'] as String,
    );
  }
}
