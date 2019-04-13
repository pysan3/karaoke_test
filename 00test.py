# m = int(input())

# counter = 0
# for n in range(1, m+1, 2):
#     c = 1
#     for i in range(2, int(n**0.5)):
#         if n % i == 0:
#             c += 1
#     if c == 4:
#         counter += 1

# print(counter)

# s = [int(i) for i in input()]
# k = int(input())

# count = 0
# while s[0] == 1:
#     s = s[1:]
#     count += 1
#     if len(s) == 0:
#         break
# if k <= count:
#     print(1)
# else:
#     print(s[0])

# n, m, q = (int(i) for i in input().split())
# city = [[0 for i in range(n+1)] for j in range(n+1)]

# for i in range(m):
#     l, r = (int(i) for i in input().split())
#     city[l][r] += 1
# for i in range(1, n+1):
#     for j in range(1, n+1):
#         city[i][j] += city[i][j-1]
# for i in range(1, n+1):
#     for j in range(1, n+1):
#         city[i][j] += city[i-1][j]


# for i in range(q):
#     a, b = (int(i) for i in input().split())
#     print(city[b][b] - city[a-1][b] - city[b][a-1] + city[a-1][a-1])
