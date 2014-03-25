#! /usr/bin/python3
# -*- coding: utf-8 -*-

import random, sys
import time

class A2:
    def __init__(self, number=20):
        self.number = number
        self.prev = 0
        pass

    def Prompt(self):
        v = time.time() - self.start_time
        if self.prev >= 10:
            return "(%3d) [%d:%2d \033[22;31m%3d\033[0m]\t\t\t\t" % (self.no, v / 60, v % 60, self.prev)
        else:
            return "(%3d) [%d:%2d %3d]\t\t\t\t" % (self.no, v / 60, v % 60, self.prev)

    def GetValue(self, prompt):
        prompt = "%s%s" % (self.Prompt(), prompt)
        while True:
            a = input(prompt)
            if a:
                try:
                    return int(a)
                except:
                    pass

    def Calc1(self):
            x = random.randint(1, 19)

            if x < 10:
                y = random.randint(1, 9)
            else:
                y = random.randint(1, 10 - int(x % 10))

            prompt = "%2d + %d = " % (x, y)
            v = self.GetValue(prompt)

            return x, y, v, x + y, prompt

    def Calc2(self):
            x = random.randint(11, 19)
            y = random.randint(int(x % 10), 9)
            prompt = "%2d - %d = " % (x, y)
            v = self.GetValue(prompt)

            return x, y, v, x - y, prompt

    def Calc3(self):
            x = random.randint(2, 10)
            y = random.randint(0, x)

            prompt = "%2d - %d = " % (x, y)
            v = self.GetValue(prompt)

            return x, y, v, x - y, prompt

    def Run(self):
        self.ok = 0
        self.error = 0
        errorList = []

        self.start_time = time.time()

        print("开始时间：", time.strftime('%H:%M:%S', time.localtime(self.start_time)))
        self.no = 1

        while self.no <= self.number:
            now = time.time()
            _type = random.randint(100,200) % 3
            if _type == 0:
                x, y, a, v, prompt = self.Calc1()
            elif _type == 1:
                x, y, a, v, prompt = self.Calc2()
            elif _type == 2:
                x, y, a, v, prompt = self.Calc2()

            if a == v:
                self.ok += 1
            else:
                self.error += 1
                errorList.append((x, y, a, v, prompt))
            self.prev = time.time() - now

            self.no += 1

        end_time = time.time()
        diff_time = end_time - self.start_time
        print("\n正确 %d 题， 错误 %d 题， 本次得分: %d" % (self.ok , self.error, 100 * (self.ok / self.number) ))
        print("结束时间：%s, 耗时 %d 分 %d 秒" % (time.strftime('%H:%M:%S', time.localtime(end_time)), int(diff_time / 60), int(diff_time % 60)) )

        print("错误列表：")
        for (x, y, a, v, prompt) in errorList:
            print("\t%s\033[22;31m%2d\033[0m ( %2d )" %  (prompt, a, v))

def main():
    if len(sys.argv) > 1:
        number = int(sys.argv[1])
    else:
        number = 25

    a = A2(number)
    a.Run()

if __name__ == '__main__':
    main()
