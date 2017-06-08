//UDPServer.c
 
/*
 *  gcc -o server UDPServer.c
 *  ./server
 */
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <cstdio>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#define BUFLEN 8200
#define PORT 7200
FILE *fp;
int sockfd;
unsigned int prev_cont,cont;
 
void my_handler(int s){
    close(sockfd);
    fclose(fp);
    printf("\nLast packet cont: %d\n",cont);
    printf("\n\nRegistration Terminated\n");
    exit(1); 
}

void err(char *str)
{
    perror(str);
    exit(1);
}
 
//! Byte swap unsigned int
uint32_t swap_uint32( uint32_t val )
{
    val = ((val << 8) & 0xFF00FF00 ) | ((val >> 8) & 0xFF00FF ); 
    return (val << 16) | (val >> 16);
}

int main(int argc, char *argv[])
{
    struct sockaddr_in my_addr, cli_addr;
    int  i;
    socklen_t slen=sizeof(cli_addr);
    char buf[BUFLEN];
    unsigned int *ciccio;
    //char *prog;

    struct sigaction sigIntHandler;

    sigIntHandler.sa_handler = my_handler;
    sigemptyset(&sigIntHandler.sa_mask);
    sigIntHandler.sa_flags = 0;

    sigaction(SIGINT, &sigIntHandler, NULL);

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP))==-1)
      err("socket");
    else
      printf("Server : Socket() successful\n");
 
    bzero(&my_addr, sizeof(my_addr));
    my_addr.sin_family = AF_INET;
    my_addr.sin_port = htons(PORT);
    my_addr.sin_addr.s_addr = htonl(INADDR_ANY);
     
    if (bind(sockfd, (struct sockaddr* ) &my_addr, sizeof(my_addr))==-1)
      err("bind");
    else
      printf("Server : bind() successful\n");
    //prog="./mad_header.py -o"+argv[1];
    //system("./mad_header.py -o"+argv[1]);

    fp = fopen(argv[1],"wb");
    //if (fp!=NULL){
        prev_cont=-1; 
        while(1)
        {
            if (recvfrom(sockfd, buf, BUFLEN, 0, (struct sockaddr*)&cli_addr, &slen)==-1)
                err("recvfrom()");
            ciccio = (unsigned int *)buf;
            cont = swap_uint32(ciccio[1]);
            //printf("Received packet from %s:%d\nCnt: %i\n\n",
            //       inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), swap_uint32(ciccio[1]));
            if (prev_cont==-1){
                printf("Receiving packets from %s:%d\nFirst Counter: %i\n\n",
                   inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), cont);
            }
            if ((cont != prev_cont+1)&&(prev_cont!=-1)){
                printf("*** Lost %d packets!",(cont-prev_cont));
            }
            prev_cont = cont;
            fwrite(buf, 1, sizeof(buf), fp);
            fflush(fp);
        }
        printf("\n\nQUI NON CI PASSEREMO MAI!\n");
        close(sockfd);
        fclose(fp);
   // }
    //else printf("Error on reading firmware header BRAM, program halted!");
    return 0;
}

